#!/usr/bin/env python3
"""
TikTok Seeding Detection Backend Server
Run with: python run.py
"""

import uvicorn
import sys
import os
from app.config import get_settings

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    settings = get_settings() # Lấy cấu hình
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload, # Sử dụng giá trị từ settings
        log_level=settings.log_level.lower()
    )