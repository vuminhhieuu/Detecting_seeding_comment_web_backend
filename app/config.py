import os
from typing import Optional, List, Dict
from pydantic_settings import BaseSettings
from pydantic import Field # Import Field nếu bạn muốn dùng alias cho biến môi trường

# Biến toàn cục để quản lý token hiện tại
_current_token_index = 0
_token_pool: List[str] = []

class Settings(BaseSettings):
    """Application settings"""

    # API Configuration
    app_name: str = "TikTok Seeding Detection API"
    app_version: str = "1.0.0"
    debug: bool = False

    # Server Configuration
    host: str = "0.0.0.0"
    port: int = int(os.getenv("PORT", 8000))
    reload: bool = False # Nên là False cho production

    # CORS Configuration
    # Giá trị mặc định này sẽ được ghi đè bởi biến môi trường CORS_ORIGINS
    cors_origins: List[str] = Field(default_factory=lambda: ["http://localhost:5173", "http://localhost:3000"])
    cors_allow_credentials: bool = True
    cors_allow_methods: List[str] = ["*"]
    cors_allow_headers: List[str] = ["*"]

    # Rate Limiting
    rate_limit_requests: int = 100
    rate_limit_window: int = 3600  # 1 hour

    # ML Model Configuration
    huggingface_api_url: str = "https://api-inference.huggingface.co/models/minhhieu2610/visobert_comments_seeding"
    huggingface_token: Optional[str] = None # Sẽ được load từ env
    model_timeout: int = 30

    # TikTok API Configuration
    tiktok_api_timeout: int = 30
    max_comments_per_video: int = 10000 # Có thể điều chỉnh cho phù hợp
    ms_token: Optional[str] = None # Ưu tiên load từ env hoặc pool, không hardcode ở đây
    tiktok_ms_token_pool_str: Optional[str] = Field(default=None, alias="TIKTOK_MS_TOKEN_POOL_STR") # Load từ env
    max_comments_to_crawl: int = 10000

    # File Upload Configuration
    max_file_size_mb: int = 10
    allowed_file_types: List[str] = [".json", ".csv"]

    # Cache Configuration
    cache_ttl: int = 3600  # 1 hour
    cache_max_size: int = 1000

    # Database Configuration (for future use)
    database_url: Optional[str] = None

    # Logging Configuration
    log_level: str = "INFO"
    log_format: str = "json" # Hoặc "text"

    # Security
    secret_key: str = "your-secret-key-needs-to-be-changed-in-production" # Sẽ được load từ env
    access_token_expire_minutes: int = 30

    # Analysis Configuration
    max_batch_size: int = 1000
    confidence_threshold: float = 0.5

    # Proxy Configuration
    proxy_address: Optional[str] = None
    proxy_port: Optional[int] = None
    proxy_username: Optional[str] = None
    proxy_password: Optional[str] = None

    @property
    def httpx_proxies(self) -> Optional[Dict[str, str]]:
        if self.proxy_address and self.proxy_port:
            base_proxy_url_part = f"{self.proxy_address}:{self.proxy_port}"
            if self.proxy_username and self.proxy_password:
                proxy_url = f"http://{self.proxy_username}:{self.proxy_password}@{base_proxy_url_part}"
            else:
                # Cho proxy không cần xác thực, hoặc nếu username/password được nhúng trong address
                proxy_url = f"http://{base_proxy_url_part}"
            
            return {
                "http://": proxy_url,
                "https://": proxy_url, # HTTPS traffic cũng đi qua proxy HTTP này
            }
        return None

    class Config:
        env_file = ".env" # Đường dẫn đến file .env
        env_file_encoding = "utf-8"
        extra = "ignore" # Bỏ qua các biến môi trường không được định nghĩa trong Settings
        # Cho phép Pydantic đọc các biến môi trường không phân biệt chữ hoa chữ thường
        case_sensitive = False


# Global settings instance
settings = Settings()

def get_settings() -> Settings:
    """Get application settings"""
    return settings

def _initialize_token_pool():
    """Khởi tạo token pool từ chuỗi trong settings."""
    global _token_pool, settings
    if not _token_pool and settings.tiktok_ms_token_pool_str:
        _token_pool = [token.strip() for token in settings.tiktok_ms_token_pool_str.split(',') if token.strip()]
        # print(f"DEBUG: Token pool initialized with {len(_token_pool)} tokens.") # Bỏ comment để debug

def load_and_get_tiktok_token() -> Optional[str]:
    """
    Lấy token hiện tại từ pool. Nếu pool rỗng hoặc không được cấu hình,
    sẽ fallback về giá trị của settings.ms_token (nếu có).
    """
    global _token_pool, _current_token_index, settings
    _initialize_token_pool() # Đảm bảo pool được khởi tạo

    if _token_pool: # Ưu tiên pool nếu có token
        if _current_token_index < len(_token_pool):
            selected_token = _token_pool[_current_token_index]
            # print(f"DEBUG: Using token from pool at index {_current_token_index}: {selected_token[:15]}...") # Bỏ comment để debug
            return selected_token
        else:
            # print(f"DEBUG: Current token index {_current_token_index} out of bounds for pool size {len(_token_pool)}. Resetting index.") # Bỏ comment để debug
            _current_token_index = 0 # Reset index nếu nó vượt quá giới hạn (có thể xảy ra nếu pool thay đổi)
            if _token_pool: # Thử lại với index đã reset
                 selected_token = _token_pool[_current_token_index]
                 # print(f"DEBUG: Using token from pool at reset index {_current_token_index}: {selected_token[:15]}...") # Bỏ comment để debug
                 return selected_token

    # Fallback về ms_token đơn lẻ nếu pool không có hoặc không lấy được token từ pool
    if settings.ms_token:
        # print(f"DEBUG: Falling back to single ms_token: {settings.ms_token[:15]}...") # Bỏ comment để debug
        return settings.ms_token
    
    # print("DEBUG: No TikTok msToken available (pool is empty and single ms_token is not set).") # Bỏ comment để debug
    return None

def rotate_tiktok_token() -> bool:
    """
    Xoay vòng sang token tiếp theo trong pool.
    Trả về True nếu xoay vòng thành công, False nếu pool rỗng.
    """
    global _current_token_index, _token_pool
    _initialize_token_pool() # Đảm bảo pool được khởi tạo

    if not _token_pool or len(_token_pool) == 0:
        # print("DEBUG: Cannot rotate, token pool is empty.") # Bỏ comment để debug
        return False 
    
    _current_token_index = (_current_token_index + 1) % len(_token_pool)
    # print(f"DEBUG: Rotated TikTok msToken to index: {_current_token_index}") # Bỏ comment để debug
    return True

# Khởi tạo pool token một lần khi module này được load (tùy chọn)
# Hoặc để _initialize_token_pool() được gọi khi cần trong load_and_get_tiktok_token()
# _initialize_token_pool()