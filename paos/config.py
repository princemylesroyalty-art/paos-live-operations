import os
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # API
    api_title: str = "PAOS Live Operations"
    api_version: str = "0.1.0"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    debug: bool = os.getenv("DEBUG", "false").lower() == "true"
    
    # Database
    database_url: str = os.getenv(
        "DATABASE_URL",
        "postgresql://paos:paospass@localhost:5432/paos_operations"
    )
    
    # Redis
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    
    # AI Providers
    openai_api_key: Optional[str] = os.getenv("OPENAI_API_KEY")
    anthropic_api_key: Optional[str] = os.getenv("ANTHROPIC_API_KEY")
    
    # Security
    secret_key: str = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Encryption for connections
    encryption_key: str = os.getenv("ENCRYPTION_KEY", "dev-encryption-key-32-chars-long-!")
    
    # Agent Configuration
    max_agent_iterations: int = 10
    agent_timeout_seconds: int = 300
    
    # Approval Settings
    require_approval_for_communicate: bool = True
    require_approval_for_purchase: bool = True
    require_approval_for_financial: bool = True
    require_approval_for_irreversible: bool = True
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
