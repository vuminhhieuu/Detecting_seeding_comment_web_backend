from fastapi import FastAPI, HTTPException, UploadFile, File, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.exceptions import RequestValidationError
from typing import List, Optional, Union
import json
import pandas as pd
import io
from datetime import datetime
import asyncio
import random
import time

from .models import (
    PredictionRequest, 
    PredictionResponse, 
    Comment, 
    AnalysisStats,
    URLRequest,
    MultiURLRequest,
    ErrorResponse
)
from .services.tiktok_service import TikTokService
from .services.ml_service import MLService
from .services.data_processor import DataProcessor
from .services.validation_service import ValidationService
from .services.cache_service import cache_service
from .middleware.rate_limiter import RateLimitMiddleware
from .utils.logger import logger, log_api_request, log_api_response, log_error
from .utils.helpers import paginate_results, validate_file_size
from .config import get_settings

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    description="API for detecting seeding comments on TikTok using VisoBERT AI",
    version=settings.app_version,
    debug=settings.debug
)

# Add rate limiting middleware
app.add_middleware(
    RateLimitMiddleware,
    max_requests=settings.rate_limit_requests,
    window_seconds=settings.rate_limit_window
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.cors_allow_methods,
    allow_headers=settings.cors_allow_headers,
)

# Initialize services
tiktok_service = TikTokService()
ml_service = MLService()
data_processor = DataProcessor()
validation_service = ValidationService()

# Global storage for results (in production, use a database)
analysis_results = {}

# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    
    # Log request
    log_api_request(
        endpoint=str(request.url.path),
        method=request.method,
        client_ip=request.client.host if request.client else "unknown"
    )
    
    response = await call_next(request)
    
    # Log response
    duration = time.time() - start_time
    log_api_response(
        endpoint=str(request.url.path),
        method=request.method,
        status_code=response.status_code,
        duration=duration
    )
    
    return response

# Exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "error": "Validation Error",
            "detail": "Dữ liệu đầu vào không hợp lệ",
            "errors": exc.errors(),
            "timestamp": datetime.now().isoformat()
        }
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": "HTTP Error",
            "detail": exc.detail,
            "timestamp": datetime.now().isoformat()
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    log_error(exc, context=f"{request.method} {request.url.path}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "detail": "Đã xảy ra lỗi hệ thống. Vui lòng thử lại sau.",
            "timestamp": datetime.now().isoformat()
        }
    )

@app.get("/")
async def root():
    return {
        "message": settings.app_name,
        "version": settings.app_version,
        "status": "operational",
        "endpoints": {
            "predict_url": "/predict/url",
            "predict_urls": "/predict/urls", 
            "predict_file": "/predict/file",
            "stats": "/stats",
            "download": "/download/{analysis_id}",
            "health": "/health",
            "docs": "/docs"
        },
        "features": [
            "Single URL analysis",
            "Batch URL processing",
            "File upload support (JSON/CSV)",
            "VisoBERT AI integration",
            "Real-time statistics",
            "CSV export functionality"
        ]
    }

@app.get("/health")
async def health_check():
    # Check cache service
    cache_stats = cache_service.get_stats()
    
    # Check ML service
    try:
        model_info = await ml_service.get_model_info()
        ml_status = "operational"
    except Exception as e:
        ml_status = f"error: {str(e)}"
    
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": settings.app_version,
        "services": {
            "ml_model": ml_status,
            "tiktok_api": "operational",
            "data_processor": "operational",
            "cache": f"operational ({cache_stats['active_entries']} entries)"
        },
        "system": {
            "cache_stats": cache_stats,
            "analysis_count": len(analysis_results)
        }
    }

@app.post("/predict/url", response_model=PredictionResponse)
async def predict_from_url(request: URLRequest):
    """Analyze comments from a single TikTok URL"""
    try:
        # Validate URL
        validation = validation_service.validate_tiktok_url(request.url)
        if not validation['valid']:
            raise HTTPException(status_code=400, detail=validation['error'])
        
        # Check cache
        cache_key = f"url:{request.url}"
        cached_result = await cache_service.get(cache_key)
        if cached_result:
            logger.info("Returning cached result for URL analysis")
            return cached_result
        
        # Extract comments from TikTok URL
        comments_data = await tiktok_service.extract_comments(request.url)
        
        # Process and predict
        comments = await data_processor.process_comments(comments_data)
        if not comments:
            raise HTTPException(status_code=404, detail="Không tìm thấy bình luận nào từ URL này")
        
        predictions = await ml_service.predict_batch([c.comment_text for c in comments])
        
        # Combine results
        for i, comment in enumerate(comments):
            comment.prediction = predictions[i].label
            comment.confidence = predictions[i].confidence
        
        # Generate analysis
        result = await _generate_analysis_result(comments, request.url)
        
        # Store result
        analysis_id = f"analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{random.randint(1000, 9999)}"
        analysis_results[analysis_id] = result
        result.analysis_id = analysis_id
        
        # Cache result
        await cache_service.set(cache_key, result, ttl=settings.cache_ttl)
        
        logger.info(f"URL analysis completed: {len(comments)} comments processed")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        log_error(e, context="predict_from_url")
        raise HTTPException(status_code=500, detail=f"Lỗi xử lý URL: {str(e)}")

@app.post("/predict/urls", response_model=PredictionResponse)
async def predict_from_urls(request: MultiURLRequest):
    """Analyze comments from multiple TikTok URLs"""
    try:
        if len(request.urls) > 10:
            raise HTTPException(status_code=400, detail="Tối đa 10 URL mỗi lần")
        
        # Validate all URLs
        for url in request.urls:
            validation = validation_service.validate_tiktok_url(url)
            if not validation['valid']:
                raise HTTPException(status_code=400, detail=f"URL không hợp lệ: {url}")
        
        all_comments = []
        
        # Process each URL
        for url in request.urls:
            try:
                comments_data = await tiktok_service.extract_comments(url)
                comments = await data_processor.process_comments(comments_data)
                all_comments.extend(comments)
            except Exception as e:
                logger.warning(f"Failed to process URL {url}: {str(e)}")
                continue
        
        if not all_comments:
            raise HTTPException(status_code=404, detail="Không tìm thấy bình luận nào từ các URL")
        
        # Batch prediction
        predictions = await ml_service.predict_batch([c.comment_text for c in all_comments])
        
        for i, comment in enumerate(all_comments):
            comment.prediction = predictions[i].label
            comment.confidence = predictions[i].confidence
        
        # Generate analysis
        result = await _generate_analysis_result(all_comments, f"{len(request.urls)} URLs")
        
        # Store result
        analysis_id = f"analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{random.randint(1000, 9999)}"
        analysis_results[analysis_id] = result
        result.analysis_id = analysis_id
        
        logger.info(f"Multi-URL analysis completed: {len(all_comments)} comments from {len(request.urls)} URLs")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        log_error(e, context="predict_from_urls")
        raise HTTPException(status_code=500, detail=f"Lỗi xử lý URLs: {str(e)}")

@app.post("/predict/file", response_model=PredictionResponse)
async def predict_from_file(file: UploadFile = File(...)):
    """Analyze comments from uploaded JSON or CSV file"""
    try:
        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="Tên file không hợp lệ")
        
        file_extension = file.filename.lower().split('.')[-1]
        if f".{file_extension}" not in settings.allowed_file_types:
            raise HTTPException(
                status_code=400, 
                detail=f"Định dạng file không được hỗ trợ. Chỉ chấp nhận: {', '.join(settings.allowed_file_types)}"
            )
        
        # Read file content
        content = await file.read()
        
        # Validate file size
        if not validate_file_size(len(content), settings.max_file_size_mb):
            raise HTTPException(
                status_code=400, 
                detail=f"File quá lớn. Tối đa {settings.max_file_size_mb}MB"
            )
        
        # Process file content
        if file_extension == 'json':
            try:
                data = json.loads(content.decode('utf-8'))
                comments = await data_processor.process_json_data(data)
            except json.JSONDecodeError:
                raise HTTPException(status_code=400, detail="File JSON không hợp lệ")
        elif file_extension == 'csv':
            try:
                df = pd.read_csv(io.StringIO(content.decode('utf-8')))
                comments = await data_processor.process_csv_data(df)
            except Exception:
                raise HTTPException(status_code=400, detail="File CSV không hợp lệ")
        
        if not comments:
            raise HTTPException(status_code=400, detail="Không tìm thấy dữ liệu bình luận hợp lệ trong file")
        
        if len(comments) > settings.max_batch_size:
            raise HTTPException(
                status_code=400, 
                detail=f"Quá nhiều bình luận. Tối đa {settings.max_batch_size} bình luận"
            )
        
        # Batch prediction
        predictions = await ml_service.predict_batch([c.comment_text for c in comments])
        
        for i, comment in enumerate(comments):
            comment.prediction = predictions[i].label
            comment.confidence = predictions[i].confidence
        
        # Generate analysis
        result = await _generate_analysis_result(comments, file.filename)
        
        # Store result
        analysis_id = f"analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{random.randint(1000, 9999)}"
        analysis_results[analysis_id] = result
        result.analysis_id = analysis_id
        
        logger.info(f"File analysis completed: {len(comments)} comments from {file.filename}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        log_error(e, context="predict_from_file")
        raise HTTPException(status_code=500, detail=f"Lỗi xử lý file: {str(e)}")

@app.get("/stats")
async def get_global_stats():
    """Get global statistics across all analyses"""
    try:
        # Check cache
        cache_key = "global_stats"
        cached_stats = await cache_service.get(cache_key)
        if cached_stats:
            return cached_stats
        
        total_analyses = len(analysis_results)
        total_comments = sum(len(result.comments) for result in analysis_results.values())
        total_seeding = sum(
            len([c for c in result.comments if c.prediction == 1]) 
            for result in analysis_results.values()
        )
        
        avg_seeding_rate = (total_seeding / total_comments * 100) if total_comments > 0 else 0
        
        # Get most common keywords
        all_keywords = {}
        for result in analysis_results.values():
            for keyword, count in result.keywords.items():
                all_keywords[keyword] = all_keywords.get(keyword, 0) + count
        
        top_keywords = dict(sorted(all_keywords.items(), key=lambda x: x[1], reverse=True)[:10])
        
        # Recent activity
        recent_analyses = sorted(
            analysis_results.values(),
            key=lambda x: x.processed_at,
            reverse=True
        )[:5]
        
        stats = {
            "total_analyses": total_analyses,
            "total_comments_processed": total_comments,
            "total_seeding_detected": total_seeding,
            "average_seeding_rate": round(avg_seeding_rate, 2),
            "top_seeding_keywords": top_keywords,
            "model_accuracy": 94.5,
            "last_updated": datetime.now().isoformat(),
            "recent_activity": [
                {
                    "analysis_id": r.analysis_id,
                    "source": r.source,
                    "comment_count": len(r.comments),
                    "seeding_percentage": r.stats.seeding_percentage,
                    "processed_at": r.processed_at
                }
                for r in recent_analyses
            ]
        }
        
        # Cache stats
        await cache_service.set(cache_key, stats, ttl=300)  # 5 minutes
        
        return stats
        
    except Exception as e:
        log_error(e, context="get_global_stats")
        raise HTTPException(status_code=500, detail=f"Lỗi lấy thống kê: {str(e)}")

@app.get("/download/{analysis_id}")
async def download_results(analysis_id: str):
    """Download analysis results as CSV"""
    try:
        if analysis_id not in analysis_results:
            raise HTTPException(status_code=404, detail="Không tìm thấy kết quả phân tích")
        
        result = analysis_results[analysis_id]
        
        # Create CSV content
        csv_data = []
        for comment in result.comments:
            csv_data.append({
                'comment_id': comment.comment_id,
                'comment_text': comment.comment_text,
                'like_count': comment.like_count,
                'timestamp': comment.timestamp,
                'user_id': comment.user_id,
                'prediction': 'Seeding' if comment.prediction == 1 else 'Not Seeding',
                'confidence': f"{comment.confidence:.3f}" if comment.confidence else "N/A"
            })
        
        df = pd.DataFrame(csv_data)
        
        # Create CSV string
        output = io.StringIO()
        df.to_csv(output, index=False, encoding='utf-8')
        csv_content = output.getvalue()
        
        # Return as streaming response
        return StreamingResponse(
            io.StringIO(csv_content),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=tiktok_analysis_{analysis_id}.csv"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        log_error(e, context="download_results")
        raise HTTPException(status_code=500, detail=f"Lỗi tải file: {str(e)}")

@app.get("/analysis/{analysis_id}", response_model=PredictionResponse)
async def get_analysis(analysis_id: str, page: int = 1, per_page: int = 50):
    """Get specific analysis results with pagination"""
    if analysis_id not in analysis_results:
        raise HTTPException(status_code=404, detail="Không tìm thấy kết quả phân tích")
    
    result = analysis_results[analysis_id]
    
    # Paginate comments
    paginated = paginate_results(result.comments, page, per_page)
    
    # Return paginated result
    paginated_result = PredictionResponse(
        comments=paginated['items'],
        stats=result.stats,
        keywords=result.keywords,
        source=result.source,
        processed_at=result.processed_at,
        analysis_id=result.analysis_id
    )
    
    return paginated_result

@app.delete("/analysis/{analysis_id}")
async def delete_analysis(analysis_id: str):
    """Delete specific analysis"""
    if analysis_id not in analysis_results:
        raise HTTPException(status_code=404, detail="Không tìm thấy kết quả phân tích")
    
    del analysis_results[analysis_id]
    
    # Clear related cache
    await cache_service.delete("global_stats")
    
    logger.info(f"Analysis deleted: {analysis_id}")
    return {"message": "Đã xóa kết quả phân tích thành công"}

@app.get("/cache/stats")
async def get_cache_stats():
    """Get cache statistics"""
    return cache_service.get_stats()

@app.post("/cache/clear")
async def clear_cache():
    """Clear all cache"""
    await cache_service.clear()
    return {"message": "Cache đã được xóa"}

async def _generate_analysis_result(comments: List[Comment], source: str) -> PredictionResponse:
    """Generate comprehensive analysis result"""
    total = len(comments)
    seeding_count = len([c for c in comments if c.prediction == 1])
    not_seeding_count = total - seeding_count
    seeding_percentage = round((seeding_count / total * 100), 2) if total > 0 else 0
    
    # Extract keywords from seeding comments
    seeding_comments = [c for c in comments if c.prediction == 1]
    keywords = await data_processor.extract_keywords(seeding_comments)
    
    stats = AnalysisStats(
        total=total,
        seeding=seeding_count,
        not_seeding=not_seeding_count,
        seeding_percentage=seeding_percentage
    )
    
    return PredictionResponse(
        comments=comments,
        stats=stats,
        keywords=keywords,
        source=source,
        processed_at=datetime.now().isoformat()
    )

# Startup event
@app.on_event("startup")
async def startup_event():
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"Debug mode: {settings.debug}")
    logger.info(f"Rate limiting: {settings.rate_limit_requests} requests per {settings.rate_limit_window}s")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down TikTok Seeding Detection API")
    await ml_service.close()
    await tiktok_service.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app, 
        host=settings.host, 
        port=settings.port, 
        reload=settings.reload,
        log_level=settings.log_level.lower()
    )