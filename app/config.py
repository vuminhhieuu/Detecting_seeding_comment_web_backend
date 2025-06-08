import os
from typing import Optional
from pydantic_settings import BaseSettings 

class Settings(BaseSettings):
    """Application settings"""
    
    # API Configuration
    app_name: str = "TikTok Seeding Detection API"
    app_version: str = "1.0.0"
    debug: bool = False
    
    # Server Configuration
    host: str = "0.0.0.0"
    port: int = 8000
    reload: bool = True
    
    # CORS Configuration
    cors_origins: list = ["http://localhost:5173", "http://localhost:3000", "http://localhost:8080"]
    cors_allow_credentials: bool = True
    cors_allow_methods: list = ["*"]
    cors_allow_headers: list = ["*"]
    
    # Rate Limiting
    rate_limit_requests: int = 100
    rate_limit_window: int = 3600  # 1 hour
    
    # ML Model Configuration
    huggingface_api_url: str = "https://api-inference.huggingface.co/models/minhhieu2610/visobert_comments_seeding"
    huggingface_token: Optional[str] = None
    model_timeout: int = 30
    
    # TikTok API Configuration
    tiktok_api_timeout: int = 30
    max_comments_per_video: int = 500
    ms_token: Optional[str] = "GjnAxFIL79IIy9YPdRRWw4vNzFEHVMF_iwhfHJxTTLjFm0aS-f47eNBXGYbvzHUAYjN1NjCDb9BTh6HWgkSX1WVNMjMy4kIl7JSI0nIp9mkHuOSR-_RjXCmeIvPGx_N85mg5k8jogHAcDsxNdxPCXxMUJw==" 
    max_comments_to_crawl: int = 10000
    
    # File Upload Configuration
    max_file_size_mb: int = 10
    allowed_file_types: list = [".json", ".csv"]
    
    # Cache Configuration
    cache_ttl: int = 3600  # 1 hour
    cache_max_size: int = 1000
    
    # Database Configuration (for future use)
    database_url: Optional[str] = None
    
    # Logging Configuration
    log_level: str = "INFO"
    log_format: str = "json"
    
    # Security
    secret_key: str = "your-secret-key-change-in-production"
    access_token_expire_minutes: int = 30
    
    # Analysis Configuration
    max_batch_size: int = 1000
    confidence_threshold: float = 0.5
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

# Global settings instance
settings = Settings()

def get_settings() -> Settings:
    """Get application settings"""
    return settings