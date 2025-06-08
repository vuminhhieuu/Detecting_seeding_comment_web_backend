import re
import hashlib
from datetime import datetime
from typing import List, Dict, Any, Optional
import unicodedata

def normalize_vietnamese_text(text: str) -> str:
    """Normalize Vietnamese text for better processing"""
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text.strip())
    
    # Normalize unicode characters
    text = unicodedata.normalize('NFC', text)
    
    # Remove special characters but keep Vietnamese diacritics
    text = re.sub(r'[^\w\s\u00C0-\u024F\u1E00-\u1EFF]', ' ', text)
    
    return text.strip()

def extract_hashtags(text: str) -> List[str]:
    """Extract hashtags from text"""
    hashtag_pattern = r'#[\w\u00C0-\u024F\u1E00-\u1EFF]+'
    hashtags = re.findall(hashtag_pattern, text, re.IGNORECASE)
    return [tag.lower() for tag in hashtags]

def extract_mentions(text: str) -> List[str]:
    """Extract @mentions from text"""
    mention_pattern = r'@[\w\u00C0-\u024F\u1E00-\u1EFF]+'
    mentions = re.findall(mention_pattern, text, re.IGNORECASE)
    return [mention.lower() for mention in mentions]

def calculate_text_similarity(text1: str, text2: str) -> float:
    """Calculate similarity between two texts using simple word overlap"""
    words1 = set(normalize_vietnamese_text(text1).lower().split())
    words2 = set(normalize_vietnamese_text(text2).lower().split())
    
    if not words1 or not words2:
        return 0.0
    
    intersection = words1.intersection(words2)
    union = words1.union(words2)
    
    return len(intersection) / len(union) if union else 0.0

def generate_content_hash(content: str) -> str:
    """Generate hash for content deduplication"""
    normalized = normalize_vietnamese_text(content).lower()
    return hashlib.md5(normalized.encode('utf-8')).hexdigest()

def detect_spam_indicators(text: str) -> Dict[str, Any]:
    """Detect various spam indicators in text"""
    indicators = {
        'excessive_caps': False,
        'excessive_punctuation': False,
        'repeated_chars': False,
        'url_present': False,
        'phone_number': False,
        'excessive_emojis': False
    }
    
    # Excessive caps (more than 50% uppercase)
    if text.isupper() and len(text) > 10:
        indicators['excessive_caps'] = True
    
    # Excessive punctuation
    punct_count = len(re.findall(r'[!?.,;:]', text))
    if punct_count > len(text) * 0.3:
        indicators['excessive_punctuation'] = True
    
    # Repeated characters (3+ consecutive same chars)
    if re.search(r'(.)\1{2,}', text):
        indicators['repeated_chars'] = True
    
    # URL detection
    if re.search(r'http[s]?://|www\.|\.com|\.vn', text, re.IGNORECASE):
        indicators['url_present'] = True
    
    # Phone number detection (Vietnamese format)
    if re.search(r'(\+84|0)[0-9]{8,10}', text):
        indicators['phone_number'] = True
    
    # Excessive emojis (more than 30% of text)
    emoji_count = len(re.findall(r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF]', text))
    if emoji_count > len(text.split()) * 0.3:
        indicators['excessive_emojis'] = True
    
    return indicators

def format_timestamp(timestamp: str) -> str:
    """Format timestamp to Vietnamese locale"""
    try:
        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        return dt.strftime('%d/%m/%Y %H:%M')
    except:
        return timestamp

def calculate_engagement_score(like_count: int, comment_length: int) -> float:
    """Calculate engagement score based on likes and comment length"""
    # Normalize comment length (longer comments might get more engagement)
    length_factor = min(comment_length / 100, 1.0)
    
    # Log scale for likes to prevent extreme values
    import math
    like_factor = math.log10(max(like_count, 1))
    
    return round((like_factor * length_factor), 2)

def extract_keywords_simple(text: str, min_length: int = 3) -> List[str]:
    """Simple keyword extraction from text"""
    # Vietnamese stop words
    stop_words = {
        'và', 'của', 'có', 'là', 'được', 'một', 'trong', 'với', 'để', 'cho',
        'từ', 'này', 'đó', 'các', 'những', 'khi', 'nếu', 'như', 'về', 'theo',
        'tôi', 'bạn', 'anh', 'chị', 'em', 'mình', 'họ', 'chúng', 'ta', 'rất',
        'quá', 'lắm', 'nhiều', 'ít', 'cũng', 'đã', 'sẽ', 'đang', 'thì'
    }
    
    # Normalize and split text
    normalized = normalize_vietnamese_text(text.lower())
    words = normalized.split()
    
    # Filter keywords
    keywords = [
        word for word in words
        if len(word) >= min_length and word not in stop_words and word.isalpha()
    ]
    
    return keywords

def paginate_results(items: List[Any], page: int = 1, per_page: int = 50) -> Dict[str, Any]:
    """Paginate a list of items"""
    total = len(items)
    start = (page - 1) * per_page
    end = start + per_page
    
    return {
        'items': items[start:end],
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': total,
            'pages': (total + per_page - 1) // per_page,
            'has_next': end < total,
            'has_prev': page > 1
        }
    }

def validate_file_size(file_size: int, max_size_mb: int = 10) -> bool:
    """Validate file size"""
    max_size_bytes = max_size_mb * 1024 * 1024
    return file_size <= max_size_bytes

def safe_int(value: Any, default: int = 0) -> int:
    """Safely convert value to integer"""
    try:
        return int(value)
    except (ValueError, TypeError):
        return default

def safe_float(value: Any, default: float = 0.0) -> float:
    """Safely convert value to float"""
    try:
        return float(value)
    except (ValueError, TypeError):
        return default