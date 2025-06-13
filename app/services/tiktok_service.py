import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import httpx

from TikTokApi import TikTokApi as OfficialTikTokApi
from TikTokApi.exceptions import TikTokException, EmptyResponseException

from ..models import Comment, TikTokVideoInfo
from ..config import Settings, get_settings, load_and_get_tiktok_token, rotate_tiktok_token


class TikTokService:
    def __init__(self):
        self.settings: Settings = get_settings()
        self.logger = logging.getLogger(__name__)
        self.max_token_rotation_attempts = 3  # Số lần tối đa thử xoay vòng token
        
        if not self.settings.ms_token and not self.settings.tiktok_ms_token_pool_str:
            self.logger.warning(
                "Neither MS_TOKEN nor TIKTOK_MS_TOKEN_POOL_STR is configured. "
                "TikTok crawling will likely fail. Please set at least one in your .env file or config."
            )
        
        proxy_config = self.settings.httpx_proxies
        if proxy_config:
            safe_proxy_config = {k: v.replace(self.settings.proxy_password, "****") 
                               if self.settings.proxy_password and self.settings.proxy_password in v else v 
                               for k, v in proxy_config.items()}
            self.logger.info(f"Proxy configuration is available: {safe_proxy_config}")
        else:
            self.logger.warning("No proxy configuration found. TikTok might block requests.")

    async def extract_comments(self, url: str) -> List[Dict[str, Any]]:
        comments_data: List[Dict[str, Any]] = []
        self.logger.info(f"Attempting to crawl comments for URL: {url}")
        
        proxy_config = self.settings.httpx_proxies
        
        for attempt in range(self.max_token_rotation_attempts):
            current_token = load_and_get_tiktok_token()
            if not current_token:
                self.logger.error("No valid msToken available. Cannot fetch comments.")
                return []
            
            api_instance = None 
            try:
                self.logger.info(f"Attempt {attempt + 1}/{self.max_token_rotation_attempts} using msToken and proxy")
                
                # Khởi tạo TikTokApi
                api_instance = OfficialTikTokApi() 
                
                # ms_token được truyền vào create_sessions
                await api_instance.create_sessions(
                    ms_tokens=[current_token, ], 
                    num_sessions=1, 
                    headless=True,
                    sleep_after=3,
                    proxies=proxy_config if proxy_config else None
                )
                
                video = api_instance.video(url=url) 
                
                comment_count_api = 0
                async for comment_raw in video.comments(count=self.settings.max_comments_to_crawl):
                    comment_dict_api = comment_raw.as_dict
                    user_info = comment_dict_api.get("user", {})
                    timestamp_unix = comment_dict_api.get("create_time")
                    timestamp_iso = datetime.fromtimestamp(timestamp_unix).isoformat() if timestamp_unix else datetime.now().isoformat()

                    comment_obj = {
                        "comment_id": comment_dict_api.get("cid", f"generated_cid_{comment_count_api}"),
                        "comment_text": comment_dict_api.get("text", ""),
                        "like_count": comment_dict_api.get("digg_count", 0),
                        "timestamp": timestamp_iso,
                        "user_id": user_info.get("id", user_info.get("unique_id", f"generated_user_{comment_count_api}")),
                    }
                    comments_data.append(comment_obj)
                    comment_count_api += 1
                    if comment_count_api % 20 == 0:
                        self.logger.info(f"Crawled {comment_count_api} comments for video...")
                
                self.logger.info(f"Successfully crawled {len(comments_data)} comments for video URL: {url}")
                break
                
            except EmptyResponseException as e:
                self.logger.warning(f"TikTok returned empty response (attempt {attempt + 1}): {e}")
                if attempt < self.max_token_rotation_attempts - 1:
                    self.logger.info("Rotating to next token and retrying...")
                    if not rotate_tiktok_token():
                        self.logger.error("Failed to rotate token (pool may be empty). Giving up.")
                        break
                else:
                    self.logger.error(f"Max retry attempts reached. Failed to crawl using any available token.")
            
            except TikTokException as e:
                self.logger.error(f"TikTok API error while extracting comments for {url} (attempt {attempt + 1}): {e}")
                if attempt < self.max_token_rotation_attempts - 1:
                    self.logger.info("This might be a token issue. Rotating to next token and retrying...")
                    if not rotate_tiktok_token():
                        self.logger.error("Failed to rotate token (pool may be empty). Giving up.")
                        break
                else:
                    self.logger.error(f"Max retry attempts reached. Failed to crawl using any available token.")
            
            except httpx.ProxyError as e:
                self.logger.error(f"Proxy error while crawling comments: {e}")
                break
                
            except Exception as e:
                self.logger.error(f"Unexpected error while extracting comments for {url} (attempt {attempt + 1}): {e}", exc_info=True)
                if attempt < self.max_token_rotation_attempts - 1:
                    self.logger.info("Retrying with same token...")
                else:
                    self.logger.error("Max retry attempts reached.")
            
            finally:
                if api_instance:
                    pass 
                    
        return comments_data
    
    async def get_video_info(self, url: str) -> Optional[TikTokVideoInfo]:
        self.logger.info(f"Attempting to fetch video info for URL: {url}")
        
        proxy_config = self.settings.httpx_proxies
        
        for attempt in range(self.max_token_rotation_attempts):
            current_token = load_and_get_tiktok_token()
            if not current_token:
                self.logger.error("No valid msToken available. Cannot fetch video info.")
                return None
            
            api_instance = None
            try:
                self.logger.info(f"Attempt {attempt + 1}/{self.max_token_rotation_attempts} to fetch video info")
                
                # Khởi tạo TikTokApi
                api_instance = OfficialTikTokApi()
                
                 # Cấu hình proxy cho api_instance (nếu có)
                if proxy_config:
                    api_instance.proxies = proxy_config
                
                # ms_token được truyền vào create_sessions
                await api_instance.create_sessions(
                    ms_tokens=[current_token], 
                    num_sessions=1, 
                    headless=True,
                    sleep_after=3
                    # proxy=proxy_config # Xóa proxy khỏi đây
                )
                
                video_obj_api = api_instance.video(url=url)
                video_info_api = await video_obj_api.info() 
                
                author_info = video_info_api.get("author", {})
                stats_info = video_info_api.get("stats", {})
                created_time_unix = video_info_api.get("createTime")
                created_at_iso = datetime.fromtimestamp(created_time_unix).isoformat() if created_time_unix else datetime.now().isoformat()

                video_data = TikTokVideoInfo(
                    video_id=video_info_api.get("id", "unknown_id"),
                    author=author_info.get("uniqueId", author_info.get("nickname", "unknown_author")),
                    description=video_info_api.get("desc", ""),
                    like_count=stats_info.get("diggCount", 0),
                    comment_count=stats_info.get("commentCount", 0),
                    share_count=stats_info.get("shareCount", 0),
                    play_count=stats_info.get("playCount", 0),
                    created_at=created_at_iso
                )
                self.logger.info(f"Successfully fetched video info for ID: {video_data.video_id}")
                return video_data

            except EmptyResponseException as e:
                self.logger.warning(f"TikTok returned empty response for video info (attempt {attempt + 1}): {e}")
                if attempt < self.max_token_rotation_attempts - 1:
                    self.logger.info("Rotating to next token and retrying...")
                    if not rotate_tiktok_token():
                        self.logger.error("Failed to rotate token (pool may be empty). Giving up.")
                        break
                else:
                    self.logger.error(f"Max retry attempts reached. Failed to get video info using any available token.")

            except TikTokException as e:
                self.logger.error(f"TikTok API error while fetching video info for {url} (attempt {attempt + 1}): {e}")
                if attempt < self.max_token_rotation_attempts - 1:
                    self.logger.info("This might be a token issue. Rotating to next token and retrying...")
                    if not rotate_tiktok_token():
                        self.logger.error("Failed to rotate token (pool may be empty). Giving up.")
                        break
                else:
                    self.logger.error(f"Max retry attempts reached. Failed to get video info using any available token.")
            
            except httpx.ProxyError as e:
                self.logger.error(f"Proxy error while fetching video info: {e}")
                break
                
            except Exception as e:
                self.logger.error(f"Unexpected error while fetching video info for {url} (attempt {attempt + 1}): {e}", exc_info=True)
                if attempt < self.max_token_rotation_attempts - 1:
                    self.logger.info("Retrying with same token...")
                else:
                    self.logger.error("Max retry attempts reached.")
            
            finally:
                if api_instance:
                    pass 
        
        return None
    
    async def close(self):
        pass

class TikTokCrawlError(Exception):
    pass

class TikTokProxyError(TikTokCrawlError):
    pass

class TikTokTokenError(TikTokCrawlError):
    pass