import time
from typing import Dict, List
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

class RateLimiter:
    """Simple rate limiter implementation"""
    
    def __init__(self, max_requests: int = 100, window_seconds: int = 3600):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: Dict[str, List[float]] = {}
    
    def is_allowed(self, client_ip: str) -> bool:
        """Check if request is allowed for client IP"""
        now = time.time()
        
        # Initialize if first request from this IP
        if client_ip not in self.requests:
            self.requests[client_ip] = []
        
        # Clean old requests outside the window
        self.requests[client_ip] = [
            req_time for req_time in self.requests[client_ip]
            if now - req_time < self.window_seconds
        ]
        
        # Check if under limit
        if len(self.requests[client_ip]) < self.max_requests:
            self.requests[client_ip].append(now)
            return True
        
        return False
    
    def get_reset_time(self, client_ip: str) -> int:
        """Get time until rate limit resets"""
        if client_ip not in self.requests or not self.requests[client_ip]:
            return 0
        
        oldest_request = min(self.requests[client_ip])
        reset_time = oldest_request + self.window_seconds
        return max(0, int(reset_time - time.time()))

class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware"""
    
    def __init__(self, app, max_requests: int = 100, window_seconds: int = 3600):
        super().__init__(app)
        self.rate_limiter = RateLimiter(max_requests, window_seconds)
    
    async def dispatch(self, request: Request, call_next):
        # Get client IP
        client_ip = request.client.host if request.client else "unknown"
        
        # Skip rate limiting for health checks
        if request.url.path in ["/health", "/", "/docs", "/redoc"]:
            return await call_next(request)
        
        # Check rate limit
        if not self.rate_limiter.is_allowed(client_ip):
            reset_time = self.rate_limiter.get_reset_time(client_ip)
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Try again in {reset_time} seconds.",
                headers={"Retry-After": str(reset_time)}
            )
        
        response = await call_next(request)
        return response