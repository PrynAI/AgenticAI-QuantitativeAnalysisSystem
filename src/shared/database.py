"""
Database service and durable job queue management.

This module stores completed reports and also coordinates queued analysis jobs
that are processed by a separate worker service.
"""

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import Column, DateTime, Integer, String, Text, create_engine, select
from sqlalchemy.orm import declarative_base, sessionmaker

from src.shared.config import settings

Base = declarative_base()


def utcnow() -> datetime:
    """Return a timezone-aware UTC timestamp."""
    return datetime.now(timezone.utc)


class FinancialReport(Base):
    __tablename__ = "reports_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(String(10), nullable=False, index=True)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)


class AnalysisJob(Base):
    __tablename__ = "analysis_jobs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    ticker = Column(String(10), nullable=False, index=True)
    status = Column(String(20), nullable=False, default="queued", index=True)
    report_content = Column(Text, nullable=True)
    report_url = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    worker_id = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)


class DatabaseService:
    """Database access layer for reports and durable analysis jobs."""

    _engine = None
    _SessionLocal = None

    def __init__(self):
        db_url = settings.azure_postgres_connection_string
        if not db_url:
            raise ValueError("AZURE_POSTGRES_CONNECTION_STRING is missing in configuration.")

        if db_url.startswith("postgres://"):
            db_url = db_url.replace("postgres://", "postgresql://", 1)

        if DatabaseService._engine is None or DatabaseService._SessionLocal is None:
            try:
                DatabaseService._engine = create_engine(db_url)
                DatabaseService._SessionLocal = sessionmaker(
                    bind=DatabaseService._engine,
                    expire_on_commit=False,
                )
                Base.metadata.create_all(bind=DatabaseService._engine)
            except Exception as e:
                raise RuntimeError(f"Failed to initialize database connection: {e}") from e

        self.engine = DatabaseService._engine
        self.SessionLocal = DatabaseService._SessionLocal

    def save_report(self, ticker: str, content: str) -> None:
        """Save the completed markdown report to the reports log table."""
        session = self.SessionLocal()
        try:
            new_report = FinancialReport(ticker=ticker, content=content)
            session.add(new_report)
            session.commit()
            print(f"Saved {ticker} report to Database (ID: {new_report.id})")
        except Exception as e:
            session.rollback()
            raise RuntimeError(f"Failed to save report for ticker '{ticker}': {e}") from e
        finally:
            session.close()

    def create_analysis_job(self, ticker: str) -> AnalysisJob:
        """Create a durable queued job for later worker execution."""
        session = self.SessionLocal()
        try:
            new_job = AnalysisJob(ticker=ticker.upper(), status="queued")
            session.add(new_job)
            session.commit()
            session.refresh(new_job)
            return new_job
        except Exception as e:
            session.rollback()
            raise RuntimeError(f"Failed to create analysis job for ticker '{ticker}': {e}") from e
        finally:
            session.close()

    def get_analysis_job(self, job_id: str) -> AnalysisJob | None:
        """Fetch a single analysis job by its durable identifier."""
        session = self.SessionLocal()
        try:
            return session.get(AnalysisJob, job_id)
        except Exception as e:
            raise RuntimeError(f"Failed to fetch analysis job '{job_id}': {e}") from e
        finally:
            session.close()

    def claim_next_job(self, worker_id: str) -> AnalysisJob | None:
        """Atomically claim the oldest queued job for a worker."""
        session = self.SessionLocal()
        now = utcnow()
        try:
            stmt = (
                select(AnalysisJob)
                .where(AnalysisJob.status == "queued")
                .order_by(AnalysisJob.created_at.asc())
                .with_for_update(skip_locked=True)
                .limit(1)
            )
            job = session.execute(stmt).scalars().first()
            if not job:
                return None

            job.status = "running"
            job.worker_id = worker_id
            job.started_at = now
            job.updated_at = now
            job.error_message = None
            session.commit()
            session.refresh(job)
            return job
        except Exception as e:
            session.rollback()
            raise RuntimeError(f"Failed to claim next analysis job: {e}") from e
        finally:
            session.close()

    def mark_job_completed(self, job_id: str, report_content: str, report_url: str) -> AnalysisJob:
        """Mark a running job as completed and persist final outputs."""
        session = self.SessionLocal()
        now = utcnow()
        try:
            job = session.get(AnalysisJob, job_id)
            if not job:
                raise ValueError(f"Analysis job '{job_id}' was not found.")

            job.status = "completed"
            job.report_content = report_content
            job.report_url = report_url
            job.error_message = None
            job.completed_at = now
            job.updated_at = now
            session.commit()
            session.refresh(job)
            return job
        except Exception as e:
            session.rollback()
            raise RuntimeError(f"Failed to mark analysis job '{job_id}' as completed: {e}") from e
        finally:
            session.close()

    def mark_job_failed(self, job_id: str, error_message: str) -> AnalysisJob:
        """Mark a running job as failed and persist the failure details."""
        session = self.SessionLocal()
        now = utcnow()
        try:
            job = session.get(AnalysisJob, job_id)
            if not job:
                raise ValueError(f"Analysis job '{job_id}' was not found.")

            job.status = "failed"
            job.error_message = error_message
            job.completed_at = now
            job.updated_at = now
            session.commit()
            session.refresh(job)
            return job
        except Exception as e:
            session.rollback()
            raise RuntimeError(f"Failed to mark analysis job '{job_id}' as failed: {e}") from e
        finally:
            session.close()
