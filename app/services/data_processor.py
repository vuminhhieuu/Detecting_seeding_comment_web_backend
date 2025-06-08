import pandas as pd
import json
from typing import List, Dict, Any
from datetime import datetime
import re
from collections import Counter
from ..models import Comment

class DataProcessor:
    """Service for processing and analyzing comment data"""
    
    def __init__(self):
        self.stop_words = {
            'và', 'của', 'có', 'là', 'được', 'một', 'trong', 'với', 'để', 'cho',
            'từ', 'này', 'đó', 'các', 'những', 'khi', 'nếu', 'như', 'về', 'theo',
            'tôi', 'bạn', 'anh', 'chị', 'em', 'mình', 'họ', 'chúng', 'ta'
        }
    
    async def process_comments(self, comments_data: List[Dict[str, Any]]) -> List[Comment]:
        """Process raw comment data into Comment objects"""
        comments = []
        
        for data in comments_data:
            try:
                comment = Comment(
                    comment_id=data.get('comment_id', ''),
                    comment_text=data.get('comment_text', ''),
                    like_count=data.get('like_count', 0),
                    timestamp=data.get('timestamp', datetime.now().isoformat()),
                    user_id=data.get('user_id', '')
                )
                comments.append(comment)
            except Exception as e:
                print(f"Error processing comment: {e}")
                continue
        
        return comments
    
    async def process_json_data(self, json_data: Any) -> List[Comment]:
        """Process JSON data into Comment objects"""
        if isinstance(json_data, list):
            return await self.process_comments(json_data)
        elif isinstance(json_data, dict):
            # Handle different JSON structures
            if 'comments' in json_data:
                return await self.process_comments(json_data['comments'])
            else:
                return await self.process_comments([json_data])
        else:
            raise ValueError("Invalid JSON structure")
    
    async def process_csv_data(self, df: pd.DataFrame) -> List[Comment]:
        """Process CSV DataFrame into Comment objects"""
        comments = []
        
        # Map common column names
        column_mapping = {
            'id': 'comment_id',
            'text': 'comment_text',
            'content': 'comment_text',
            'message': 'comment_text',
            'likes': 'like_count',
            'like': 'like_count',
            'time': 'timestamp',
            'date': 'timestamp',
            'created_at': 'timestamp',
            'user': 'user_id',
            'username': 'user_id',
            'author': 'user_id'
        }
        
        # Rename columns
        df_renamed = df.rename(columns=column_mapping)
        
        # Ensure required columns exist
        required_columns = ['comment_text']
        for col in required_columns:
            if col not in df_renamed.columns:
                raise ValueError(f"Required column '{col}' not found in CSV")
        
        for index, row in df_renamed.iterrows():
            try:
                comment = Comment(
                    comment_id=str(row.get('comment_id', f'csv_comment_{index}')),
                    comment_text=str(row.get('comment_text', '')),
                    like_count=int(row.get('like_count', 0)),
                    timestamp=str(row.get('timestamp', datetime.now().isoformat())),
                    user_id=str(row.get('user_id', f'csv_user_{index}'))
                )
                comments.append(comment)
            except Exception as e:
                print(f"Error processing CSV row {index}: {e}")
                continue
        
        return comments
    
    async def extract_keywords(self, comments: List[Comment]) -> Dict[str, int]:
        """Extract and count keywords from seeding comments"""
        if not comments:
            return {}
        
        # Combine all comment texts
        all_text = ' '.join([comment.comment_text.lower() for comment in comments])
        
        # Clean and tokenize
        words = self._tokenize_vietnamese(all_text)
        
        # Filter out stop words and short words
        filtered_words = [
            word for word in words 
            if len(word) > 2 and word not in self.stop_words
        ]
        
        # Count word frequencies
        word_counts = Counter(filtered_words)
        
        # Return top keywords
        return dict(word_counts.most_common(20))
    
    def _tokenize_vietnamese(self, text: str) -> List[str]:
        """Simple Vietnamese tokenization"""
        # Remove special characters and numbers
        text = re.sub(r'[^\w\s]', ' ', text)
        text = re.sub(r'\d+', '', text)
        
        # Split into words
        words = text.split()
        
        # Remove empty strings
        words = [word.strip() for word in words if word.strip()]
        
        return words
    
    async def analyze_sentiment_patterns(self, comments: List[Comment]) -> Dict[str, Any]:
        """Analyze sentiment patterns in comments"""
        positive_words = ['tốt', 'hay', 'tuyệt', 'xuất sắc', 'chất lượng', 'uy tín']
        negative_words = ['tệ', 'dở', 'kém', 'lừa đảo', 'fake', 'giả']
        
        sentiment_scores = []
        
        for comment in comments:
            text_lower = comment.comment_text.lower()
            positive_count = sum(1 for word in positive_words if word in text_lower)
            negative_count = sum(1 for word in negative_words if word in text_lower)
            
            sentiment_score = positive_count - negative_count
            sentiment_scores.append(sentiment_score)
        
        return {
            'average_sentiment': sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0,
            'positive_comments': len([s for s in sentiment_scores if s > 0]),
            'negative_comments': len([s for s in sentiment_scores if s < 0]),
            'neutral_comments': len([s for s in sentiment_scores if s == 0])
        }
    
    async def detect_spam_patterns(self, comments: List[Comment]) -> Dict[str, Any]:
        """Detect spam patterns in comments"""
        patterns = {
            'repeated_comments': 0,
            'short_comments': 0,
            'emoji_heavy': 0,
            'url_containing': 0
        }
        
        comment_texts = [c.comment_text for c in comments]
        text_counts = Counter(comment_texts)
        
        for comment in comments:
            text = comment.comment_text
            
            # Check for repeated comments
            if text_counts[text] > 1:
                patterns['repeated_comments'] += 1
            
            # Check for very short comments
            if len(text.split()) <= 2:
                patterns['short_comments'] += 1
            
            # Check for emoji-heavy comments
            emoji_count = len(re.findall(r'[😀-🙏]', text))
            if emoji_count > len(text.split()) / 2:
                patterns['emoji_heavy'] += 1
            
            # Check for URLs
            if re.search(r'http[s]?://|www\.', text):
                patterns['url_containing'] += 1
        
        return patterns
    
    async def generate_summary_report(self, comments: List[Comment]) -> Dict[str, Any]:
        """Generate comprehensive summary report"""
        total_comments = len(comments)
        seeding_comments = [c for c in comments if c.prediction == 1]
        normal_comments = [c for c in comments if c.prediction == 0]
        
        # Time analysis
        timestamps = [datetime.fromisoformat(c.timestamp.replace('Z', '+00:00')) for c in comments]
        if timestamps:
            earliest = min(timestamps)
            latest = max(timestamps)
            time_span = (latest - earliest).days
        else:
            time_span = 0
        
        # Engagement analysis
        avg_likes = sum(c.like_count for c in comments) / total_comments if total_comments > 0 else 0
        high_engagement = len([c for c in comments if c.like_count > avg_likes])
        
        return {
            'total_comments': total_comments,
            'seeding_count': len(seeding_comments),
            'normal_count': len(normal_comments),
            'time_span_days': time_span,
            'average_likes': round(avg_likes, 2),
            'high_engagement_comments': high_engagement,
            'unique_users': len(set(c.user_id for c in comments)),
            'avg_comment_length': round(sum(len(c.comment_text) for c in comments) / total_comments, 2) if total_comments > 0 else 0
        }