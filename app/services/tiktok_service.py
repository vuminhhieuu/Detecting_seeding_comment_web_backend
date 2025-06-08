import asyncio
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any
import httpx
from ..models import Comment, TikTokVideoInfo

class TikTokService:
    """Service for extracting comments from TikTok videos"""
    
    def __init__(self):
        self.base_url = "https://api.tiktok.com"  # Mock URL
        self.session = httpx.AsyncClient()
    
    async def extract_comments(self, url: str) -> List[Dict[str, Any]]:
        """
        Extract comments from TikTok video URL
        In production, this would use the unofficial TikTok API
        For now, we'll simulate realistic API response
        """
        try:
            # Simulate API delay
            await asyncio.sleep(random.uniform(1, 3))
            
            # Extract video ID from URL
            video_id = self._extract_video_id(url)
            
            # Generate realistic mock comments
            mock_comments = self._generate_realistic_comments(video_id)
            
            return mock_comments
            
        except Exception as e:
            raise Exception(f"Failed to extract comments from TikTok: {str(e)}")
    
    async def get_video_info(self, url: str) -> TikTokVideoInfo:
        """Get video metadata"""
        try:
            await asyncio.sleep(random.uniform(0.5, 1.5))
            
            video_id = self._extract_video_id(url)
            
            return TikTokVideoInfo(
                video_id=video_id,
                author=f"user_{random.randint(1000, 9999)}",
                description="Sample TikTok video description",
                like_count=random.randint(100, 10000),
                comment_count=random.randint(50, 500),
                share_count=random.randint(10, 1000),
                play_count=random.randint(1000, 100000),
                created_at=datetime.now().isoformat()
            )
            
        except Exception as e:
            raise Exception(f"Failed to get video info: {str(e)}")
    
    def _extract_video_id(self, url: str) -> str:
        """Extract video ID from TikTok URL"""
        import re
        
        # Try different TikTok URL patterns
        patterns = [
            r'/video/(\d+)',
            r'@[\w.]+/video/(\d+)',
            r'vm\.tiktok\.com/(\w+)',
            r'tiktok\.com/.*?/(\d+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        # Generate mock ID if extraction fails
        return f"video_{random.randint(100000000000000000, 999999999999999999)}"
    
    def _generate_realistic_comments(self, video_id: str) -> List[Dict[str, Any]]:
        """Generate realistic Vietnamese comments for testing"""
        
        # Realistic normal comments
        normal_comments = [
            "Video hay quá! Cảm ơn bạn đã chia sẻ",
            "Âm nhạc trong video này hay ghê!",
            "Haha clip này vui quá! 😂",
            "Cảm ơn bạn đã làm video này",
            "Mình rất thích phong cách của bạn",
            "Video chất lượng cao quá!",
            "Bạn làm video rất chuyên nghiệp",
            "Nội dung hay và bổ ích",
            "Cảm ơn bạn đã chia sẻ kiến thức",
            "Video này giúp mình học được nhiều điều",
            "Quá tuyệt vời! 👏",
            "Mình đã follow bạn rồi",
            "Chờ video tiếp theo của bạn",
            "Bạn quay ở đâu vậy? Đẹp quá!",
            "Outfit này đẹp ghê!",
            "Makeup của bạn xinh quá",
            "Bài hát gì vậy bạn?",
            "Trend này hot ghê",
            "Mình cũng muốn thử làm",
            "Bạn dạy mình được không?"
        ]
        
        # Realistic seeding comments
        seeding_comments = [
            "Sản phẩm này tuyệt vời quá! Tôi đã mua và rất hài lòng. Bạn nào cần thì inbox shop nhé! 💕",
            "Shop này uy tín lắm các bạn ơi! Tôi đã mua nhiều lần rồi, chất lượng đảm bảo 100%",
            "Link mua ở đâu vậy admin? Inbox em với ạ! Cần gấp quá 🥺",
            "Sản phẩm chất lượng cao, giá cả hợp lý. Mọi người nên mua thử!",
            "Shop bán hàng uy tín, giao hàng nhanh. Recommend cho mọi người! ⭐⭐⭐⭐⭐",
            "Mình đã order rồi, chất lượng tốt lắm. Ai cần thì liên hệ shop nhé",
            "Giá rẻ mà chất lượng tốt. Link mua ở bio shop nha các bạn!",
            "Đã test sản phẩm, hiệu quả thật sự. Bạn nào quan tâm inbox mình",
            "Shop này bán đúng như quảng cáo, không lừa đảo. Tin tưởng được!",
            "Sản phẩm hot hit này, mua ngay kẻo hết hàng. Link ở dưới comment",
            "Freeship toàn quốc, COD tận nơi. Mọi người yên tâm order nhé!",
            "Khuyến mãi 50% hôm nay thôi. Nhanh tay inbox admin!",
            "Mình bán sản phẩm này, ai cần liên hệ Zalo: 0123456789",
            "Shop cam kết hoàn tiền 100% nếu không hài lòng",
            "Đặt hàng ngay hôm nay, tặng kèm quà xinh xắn",
            "Sale sốc chỉ còn 99k, số lượng có hạn!",
            "Bạn nào ở Hà Nội mình giao tận nơi luôn",
            "Link order: bit.ly/shopuytin - Mua ngay!",
            "Admin check inbox em với, em muốn mua gấp",
            "Sản phẩm này mình đang dùng, hiệu quả lắm. Bán giá tốt!"
        ]
        
        comments = []
        num_comments = random.randint(30, 150)
        
        for i in range(num_comments):
            # 25% chance of seeding comment (realistic ratio)
            is_seeding = random.random() < 0.25
            
            if is_seeding:
                comment_text = random.choice(seeding_comments)
                # Seeding comments tend to have more likes
                like_count = random.randint(5, 300)
            else:
                comment_text = random.choice(normal_comments)
                like_count = random.randint(0, 100)
            
            # Generate realistic timestamp (last 7 days)
            days_ago = random.randint(0, 7)
            hours_ago = random.randint(0, 23)
            timestamp = datetime.now() - timedelta(days=days_ago, hours=hours_ago)
            
            comment = {
                "comment_id": f"comment_{video_id}_{i}",
                "comment_text": comment_text,
                "like_count": like_count,
                "timestamp": timestamp.isoformat(),
                "user_id": f"user_{random.randint(10000, 99999)}",
                "video_id": video_id
            }
            
            comments.append(comment)
        
        return comments
    
    async def close(self):
        """Close HTTP session"""
        await self.session.aclose()