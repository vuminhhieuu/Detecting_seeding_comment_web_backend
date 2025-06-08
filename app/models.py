from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Union
from datetime import datetime

class Comment(BaseModel):
    comment_id: str
    comment_text: str
    like_count: int = 0
    timestamp: str
    user_id: str
    prediction: Optional[int] = None  # 0 = Not Seeding, 1 = Seeding
    confidence: Optional[float] = None

class AnalysisStats(BaseModel):
    total: int
    seeding: int
    not_seeding: int
    seeding_percentage: float

class PredictionResponse(BaseModel):
    comments: List[Comment]
    stats: AnalysisStats
    keywords: Dict[str, int]
    source: str
    processed_at: str
    analysis_id: Optional[str] = None

class URLRequest(BaseModel):
    url: str = Field(..., description="TikTok video URL")

class MultiURLRequest(BaseModel):
    urls: List[str] = Field(..., description="List of TikTok video URLs")

class PredictionRequest(BaseModel):
    text: str = Field(..., description="Comment text to analyze")

class BatchPredictionRequest(BaseModel):
    texts: List[str] = Field(..., description="List of comment texts to analyze")

class MLPrediction(BaseModel):
    label: int  # 0 or 1
    confidence: float
    processing_time: float

class TikTokVideoInfo(BaseModel):
    video_id: str
    author: str
    description: str
    like_count: int
    comment_count: int
    share_count: int
    play_count: int
    created_at: str

class ErrorResponse(BaseModel):
    error: str
    detail: str
    timestamp: str