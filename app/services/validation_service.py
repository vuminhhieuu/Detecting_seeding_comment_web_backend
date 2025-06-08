import re
from typing import List, Dict, Any
from urllib.parse import urlparse
from ..models import Comment

class ValidationService:
    """Service for validating input data and URLs"""
    
    def __init__(self):
        self.tiktok_domains = [
            'tiktok.com',
            'www.tiktok.com',
            'm.tiktok.com',
            'vm.tiktok.com'
        ]
        
        # Vietnamese text patterns
        self.vietnamese_pattern = re.compile(r'[àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ]', re.IGNORECASE)
    
    def validate_tiktok_url(self, url: str) -> Dict[str, Any]:
        """Validate TikTok URL format"""
        try:
            parsed = urlparse(url)
            
            # Check domain
            if parsed.netloc.lower() not in self.tiktok_domains:
                return {
                    'valid': False,
                    'error': 'URL không phải từ TikTok'
                }
            
            # Check if it's a video URL
            if '/video/' not in parsed.path and '/@' not in parsed.path:
                return {
                    'valid': False,
                    'error': 'URL không phải là link video TikTok'
                }
            
            return {
                'valid': True,
                'video_id': self._extract_video_id(url),
                'username': self._extract_username(url)
            }
            
        except Exception as e:
            return {
                'valid': False,
                'error': f'URL không hợp lệ: {str(e)}'
            }
    
    def validate_comment_data(self, comment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate comment data structure"""
        required_fields = ['comment_text']
        optional_fields = ['comment_id', 'like_count', 'timestamp', 'user_id']
        
        errors = []
        
        # Check required fields
        for field in required_fields:
            if field not in comment_data or not comment_data[field]:
                errors.append(f'Thiếu trường bắt buộc: {field}')
        
        # Validate comment text
        if 'comment_text' in comment_data:
            text = comment_data['comment_text']
            if len(text.strip()) < 1:
                errors.append('Nội dung bình luận không được để trống')
            elif len(text) > 2000:
                errors.append('Nội dung bình luận quá dài (tối đa 2000 ký tự)')
        
        # Validate like count
        if 'like_count' in comment_data:
            try:
                like_count = int(comment_data['like_count'])
                if like_count < 0:
                    errors.append('Số lượt thích không được âm')
            except (ValueError, TypeError):
                errors.append('Số lượt thích phải là số nguyên')
        
        return {
            'valid': len(errors) == 0,
            'errors': errors
        }
    
    def validate_batch_comments(self, comments: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate a batch of comments"""
        if not comments:
            return {
                'valid': False,
                'error': 'Danh sách bình luận trống'
            }
        
        if len(comments) > 1000:
            return {
                'valid': False,
                'error': 'Quá nhiều bình luận (tối đa 1000)'
            }
        
        invalid_comments = []
        for i, comment in enumerate(comments):
            validation = self.validate_comment_data(comment)
            if not validation['valid']:
                invalid_comments.append({
                    'index': i,
                    'errors': validation['errors']
                })
        
        return {
            'valid': len(invalid_comments) == 0,
            'invalid_comments': invalid_comments,
            'total_comments': len(comments)
        }
    
    def is_vietnamese_text(self, text: str) -> bool:
        """Check if text contains Vietnamese characters"""
        return bool(self.vietnamese_pattern.search(text))
    
    def sanitize_text(self, text: str) -> str:
        """Sanitize text input"""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Remove potentially harmful characters
        text = re.sub(r'[<>"\']', '', text)
        
        return text
    
    def _extract_video_id(self, url: str) -> str:
        """Extract video ID from TikTok URL"""
        # Simple extraction - in production, use more robust parsing
        match = re.search(r'/video/(\d+)', url)
        if match:
            return match.group(1)
        return ''
    
    def _extract_username(self, url: str) -> str:
        """Extract username from TikTok URL"""
        match = re.search(r'/@([^/]+)', url)
        if match:
            return match.group(1)
        return ''