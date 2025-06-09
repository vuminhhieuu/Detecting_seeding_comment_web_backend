import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import httpx

from TikTokApi import TikTokApi as OfficialTikTokApi
from TikTokApi.exceptions import TikTokException

from ..models import Comment, TikTokVideoInfo
from ..config import Settings, get_settings


class TikTokService:
    def __init__(self):
        self.settings: Settings = get_settings()
        self.logger = logging.getLogger(__name__)
        # self.session = httpx.AsyncClient() 
        
        if not self.settings.ms_token or self.settings.ms_token == "YOUR_MS_TOKEN_HERE":
            self.logger.warning(
                "MS_TOKEN is not configured or is set to the placeholder value. "
                "TikTok crawling will likely fail. Please set it in your .env file or config."
            )

    async def extract_comments(self, url: str) -> List[Dict[str, Any]]:
        if not self.settings.ms_token or self.settings.ms_token == "YOUR_MS_TOKEN_HERE":
            self.logger.error("MS_TOKEN is not configured. Cannot fetch comments.")
            return []
        comments_data: List[Dict[str, Any]] = []
        self.logger.info(f"Attempting to crawl comments for URL: {url}")

        try:
            async with OfficialTikTokApi() as api:
                # Sử dụng context manager sẽ tự động xử lý create_sessions và cleanup
                # Đảm bảo headless=True (hoặc False nếu bạn có môi trường desktop và muốn xem trình duyệt)
                # lang có thể ảnh hưởng đến ngôn ngữ của một số metadata, không phải comment text
                await api.create_sessions(
                    ms_tokens=[self.settings.ms_token], 
                    num_sessions=1, 
                    headless=True,
                    # browser="chromium" # Cân nhắc thêm dòng này nếu vẫn gặp lỗi liên quan đến browser
                    sleep_after=3 # Thêm sleep_after từ file tham khảo
                )
                
                video = api.video(url=url)
                
                comment_count_api = 0
                async for comment_raw in video.comments(count=self.settings.max_comments_to_crawl):
                    comment_dict_api = comment_raw.as_dict
                    
                    user_info = comment_dict_api.get("user", {})
                    
                    timestamp_unix = comment_dict_api.get("create_time")
                    timestamp_iso = datetime.fromtimestamp(timestamp_unix).isoformat() if timestamp_unix else datetime.now().isoformat()

                    # Tạo dictionary với các trường bạn cần, ví dụ:
                    comment_obj = {
                        "comment_id": comment_dict_api.get("cid", f"generated_cid_{comment_count_api}"),
                        "comment_text": comment_dict_api.get("text", ""),
                        "like_count": comment_dict_api.get("digg_count", 0),
                        "timestamp": timestamp_iso,
                        "user_id": user_info.get("id", user_info.get("unique_id", f"generated_user_{comment_count_api}")),
                        # "author_username": user_info.get("unique_id"), # Thêm nếu cần
                        # "author_nickname": user_info.get("nickname"), # Thêm nếu cần
                        # "reply_count": comment_dict_api.get("reply_comment_total", 0) # Thêm nếu cần
                    }
                    comments_data.append(comment_obj)
                    comment_count_api += 1
                    if comment_count_api % 20 == 0: # Log progress
                        self.logger.info(f"Crawled {comment_count_api} comments for video...")
            
            self.logger.info(f"Successfully crawled {len(comments_data)} comments for video URL: {url}")

        except TikTokException as e:
            self.logger.error(f"TikTok API error while extracting comments for {url}: {e}")
            # Bạn có thể raise một custom exception ở đây nếu cần DataProcessor xử lý cụ thể
            # raise TikTokCrawlError(f"Failed to crawl comments: {e}")
        except Exception as e:
            self.logger.error(f"Unexpected error while extracting comments for {url}: {e}", exc_info=True)
            # raise TikTokCrawlError(f"An unexpected error occurred: {e}")
            
        return comments_data
    
    async def get_video_info(self, url: str) -> Optional[TikTokVideoInfo]:
        if not self.settings.ms_token or self.settings.ms_token == "YOUR_MS_TOKEN_HERE":
            self.logger.error("MS_TOKEN is not configured. Cannot fetch video info.")
            return None

        self.logger.info(f"Attempting to fetch video info for URL: {url}")
        try:
            async with OfficialTikTokApi() as api:
                await api.create_sessions(
                    ms_tokens=[self.settings.ms_token], 
                    num_sessions=1, 
                    headless=True,
                    # browser="chromium" # Cân nhắc thêm dòng này
                    sleep_after=3 # Thêm sleep_after từ file tham khảo
                )
                
                video_obj_api = api.video(url=url)
                video_info_api = await video_obj_api.info() # Fetches the video metadata

                # Mapping data from TikTokApi's video_info_api to your TikTokVideoInfo model
                # Tên trường có thể khác nhau tùy phiên bản TikTokApi, kiểm tra video_info_api.keys()
                
                author_info = video_info_api.get("author", {})
                stats_info = video_info_api.get("stats", {})
                
                created_time_unix = video_info_api.get("createTime") # Hoặc "create_time"
                created_at_iso = datetime.fromtimestamp(created_time_unix).isoformat() if created_time_unix else datetime.now().isoformat()

                video_data = TikTokVideoInfo(
                    video_id=video_info_api.get("id", "unknown_id"),
                    author=author_info.get("uniqueId", author_info.get("nickname", "unknown_author")), # Hoặc "unique_id"
                    description=video_info_api.get("desc", ""),
                    like_count=stats_info.get("diggCount", 0), # Hoặc "digg_count"
                    comment_count=stats_info.get("commentCount", 0), # Hoặc "comment_count"
                    share_count=stats_info.get("shareCount", 0), # Hoặc "share_count"
                    play_count=stats_info.get("playCount", 0), # Hoặc "play_count"
                    created_at=created_at_iso
                )
                self.logger.info(f"Successfully fetched video info for ID: {video_data.video_id}")
                return video_data

        except TikTokException as e:
            self.logger.error(f"TikTok API error while fetching video info for {url}: {e}")
        except Exception as e:
            self.logger.error(f"Unexpected error while fetching video info for {url}: {e}", exc_info=True)
        
        return None
    
    async def close(self):
        """Close HTTP session if it was used."""
        # if hasattr(self, 'session') and self.session:
        #     await self.session.aclose()
        #     self.logger.info("TikTokService's httpx session closed.")
        # TikTokApi's session is managed by its context manager (`async with`)
        pass

# Optional: Define custom exceptions if needed for DataProcessor to catch
# class TikTokCrawlError(Exception):
#     pass