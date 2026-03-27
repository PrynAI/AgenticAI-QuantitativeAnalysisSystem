"""
Configuration Management Module.
This code uses pydantic-settings to safely load and validate your .env file.
This module is responsible for loading, validating, and providing access to 
application settings and secrets. It uses Pydantic's BaseSettings to 
automatically read from environment variables and the .env file.

Usage:
    from src.shared.config import settings
    print(settings.openai_api_key)
"""

from functools import lru_cache
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator

class Settings(BaseSettings):
    """
    Application Settings Schema.
    
    Attributes:
        openai_api_key (str): Key for accessing OpenAI models.
        openai_model_name (str): Model identifier (e.g., 'gpt-4o').
        firecrawl_api_key (str): Key for the Firecrawl web scraping service.
    """

    # --- AI Configuration (The Brain) ---
    openai_api_key: str = Field(
        ..., 
        description="OpenAI API Key for the LLM agents."
    )
    openai_model_name: str = Field(
        ...,
        description="The OpenAI model to use for agents."
    )

    # --- Tool Configuration (The Eyes) ---
    firecrawl_api_key: str = Field(
        ..., 
        description="API Key for Firecrawl scraping service."
    )

    # --- Azure Infrastructure (The Body) ---
    azure_postgres_connection_string: Optional[str] = Field(
        None, 
        description="Connection string for Azure PostgreSQL Database."
    )
    azure_blob_storage_connection_string: Optional[str] = Field(
        None, 
        description="Connection string for Azure Blob Storage."
    )
    worker_poll_interval_seconds: int = Field(
        5,
        description="Polling interval for the background analysis worker."
    )
    job_heartbeat_interval_seconds: int = Field(
        15,
        description="How often the worker refreshes job and worker heartbeats while processing."
    )
    job_stale_after_seconds: int = Field(
        300,
        description="How long a running job can go without a heartbeat before it is re-queued."
    )
    worker_active_within_seconds: int = Field(
        60,
        description="How recently a worker heartbeat must be seen for the API to accept new jobs."
    )

    # Pydantic Config: Tells it to read from .env file
    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8",
        extra="ignore"  # Ignore extra keys in .env
    )

    @field_validator("openai_model_name", mode="before")
    @classmethod
    def validate_openai_model_name(cls, value: str | None) -> str:
        """Require OPENAI_MODEL_NAME to be explicitly set and non-empty."""
        if value is None:
            raise ValueError("OPENAI_MODEL_NAME must be set in configuration.")
        if isinstance(value, str):
            value = value.strip()
            if not value:
                raise ValueError("OPENAI_MODEL_NAME must not be blank.")
            return value
        raise ValueError("OPENAI_MODEL_NAME must be a string.")

@lru_cache()
def get_settings() -> Settings:
    """
    Creates and caches the Settings object.

    Using lru_cache ensures we only read the .env file once on startup,
    improving performance.

    Returns:
        Settings: The validated application configuration.
    """
    return Settings()

# Instantiate the settings object for easy import
settings = get_settings()
