"""Pydantic request/response models for the async job-based API."""

from datetime import datetime

from pydantic import BaseModel, Field


class AnalysisRequest(BaseModel):
    ticker: str = Field(..., description="The stock ticker symbol (e.g., NVDA, TSLA).")


class AnalysisAcceptedResponse(BaseModel):
    status: str
    job_id: str
    ticker: str
    message: str


class AnalysisStatusResponse(BaseModel):
    job_id: str
    ticker: str
    status: str
    report_content: str | None = None
    report_url: str | None = None
    error_message: str | None = None
    worker_id: str | None = None
    created_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None
