"""
API routes for submitting and polling durable analysis jobs.
"""

from fastapi import APIRouter, HTTPException, status
from starlette.concurrency import run_in_threadpool

from src.api.models import AnalysisAcceptedResponse, AnalysisRequest, AnalysisStatusResponse
from src.shared.database import AnalysisJob, DatabaseService

router = APIRouter()


def create_job(ticker: str) -> AnalysisJob:
    """Create a queued analysis job using the shared database service."""
    db = DatabaseService()
    return db.create_analysis_job(ticker)


def fetch_job(job_id: str) -> AnalysisJob | None:
    """Fetch a durable analysis job by id."""
    db = DatabaseService()
    return db.get_analysis_job(job_id)


def build_status_response(job: AnalysisJob) -> AnalysisStatusResponse:
    """Serialize ORM job state into the API response model."""
    return AnalysisStatusResponse(
        job_id=job.id,
        ticker=job.ticker,
        status=job.status,
        report_content=job.report_content,
        report_url=job.report_url,
        error_message=job.error_message,
        worker_id=job.worker_id,
        created_at=job.created_at,
        started_at=job.started_at,
        completed_at=job.completed_at,
    )


@router.post(
    "/analyze",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=AnalysisAcceptedResponse,
)
async def analyze_stock(request: AnalysisRequest):
    """
    Queue a stock analysis job and return immediately with the durable job id.
    """
    ticker = request.ticker.upper()

    try:
        job = await run_in_threadpool(create_job, ticker)
        return AnalysisAcceptedResponse(
            status=job.status,
            job_id=job.id,
            ticker=job.ticker,
            message="Analysis job accepted. Poll the job status endpoint for progress.",
        )
    except Exception as e:
        print(f"❌ API Error while queuing job: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analyze/{job_id}", response_model=AnalysisStatusResponse)
async def get_analysis_status(job_id: str):
    """
    Fetch the current status and outputs for a queued analysis job.
    """
    try:
        job = await run_in_threadpool(fetch_job, job_id)
        if not job:
            raise HTTPException(status_code=404, detail=f"Analysis job '{job_id}' was not found.")
        return build_status_response(job)
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ API Error while fetching job '{job_id}': {e}")
        raise HTTPException(status_code=500, detail=str(e))
