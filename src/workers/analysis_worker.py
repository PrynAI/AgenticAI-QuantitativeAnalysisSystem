"""
Background worker that claims queued analysis jobs and executes the pipeline.
"""

import os
import socket
import threading
import time

from dotenv import load_dotenv

from src.agents.crew import run_financial_crew
from src.shared.config import settings
from src.shared.database import DatabaseService
from src.shared.storage import StorageService

load_dotenv()


def build_worker_id() -> str:
    """Create a stable worker identifier for logs and job ownership."""
    return f"{socket.gethostname()}-{os.getpid()}"


def heartbeat_loop(
    db: DatabaseService,
    worker_id: str,
    job_id: str,
    interval_seconds: int,
    stop_event: threading.Event,
) -> None:
    """Refresh worker and job leases while a long-running analysis is in progress."""
    while not stop_event.wait(interval_seconds):
        try:
            db.heartbeat_worker(worker_id)
            db.touch_job(job_id)
        except Exception as e:
            print(f"❌ Heartbeat update failed for job {job_id}: {e}")


def process_job(db: DatabaseService, worker_id: str, job_id: str, ticker: str) -> None:
    """Run the existing analysis pipeline for a claimed job."""
    heartbeat_stop = threading.Event()
    heartbeat_interval = max(1, settings.job_heartbeat_interval_seconds)
    heartbeat_thread = threading.Thread(
        target=heartbeat_loop,
        args=(db, worker_id, job_id, heartbeat_interval, heartbeat_stop),
        daemon=True,
    )
    heartbeat_thread.start()

    try:
        result_object = run_financial_crew(ticker)
        report_text = str(result_object)

        filename = f"investment_report_{ticker}.md"
        storage = StorageService()
        blob_url = storage.upload_file(filename, filename)

        db.complete_job_with_report(
            job_id=job_id,
            ticker=ticker,
            report_content=report_text,
            report_url=blob_url,
        )
        print(f"✅ Completed analysis job {job_id} for {ticker}")
    except Exception as e:
        try:
            db.mark_job_failed(job_id=job_id, error_message=str(e))
        except Exception as mark_error:
            print(f"❌ Failed to mark job {job_id} as failed: {mark_error}")
        print(f"❌ Analysis job {job_id} for {ticker} failed: {e}")
    finally:
        heartbeat_stop.set()
        heartbeat_thread.join(timeout=heartbeat_interval + 1)
        try:
            db.heartbeat_worker(worker_id)
        except Exception as e:
            print(f"❌ Failed to refresh worker heartbeat after job {job_id}: {e}")


def run_worker() -> None:
    """Poll the durable queue table and process jobs forever."""
    db = DatabaseService()
    worker_id = build_worker_id()
    poll_interval = max(1, settings.worker_poll_interval_seconds)
    stale_after_seconds = max(settings.job_stale_after_seconds, poll_interval + 1)

    print("==================================================")
    print("     AI Financial Analyst Worker (Production)     ")
    print("==================================================")
    print(f"Worker ID: {worker_id}")
    print(f"Polling every {poll_interval} second(s)")

    while True:
        claimed_job = None
        try:
            db.heartbeat_worker(worker_id)
            recovered_jobs = db.requeue_stale_jobs(stale_after_seconds=stale_after_seconds)
            if recovered_jobs:
                print(f"Recovered {recovered_jobs} stale job(s) back to queued status.")

            claimed_job = db.claim_next_job(worker_id=worker_id)
            if not claimed_job:
                time.sleep(poll_interval)
                continue

            print(f"🚀 Claimed job {claimed_job.id} for {claimed_job.ticker}")
            process_job(db=db, worker_id=worker_id, job_id=claimed_job.id, ticker=claimed_job.ticker)
        except KeyboardInterrupt:
            print("\nWorker shutdown requested.")
            break
        except Exception as e:
            print(f"❌ Worker loop error: {e}")
            time.sleep(poll_interval)


if __name__ == "__main__":
    run_worker()
