import asyncio
import logging
import tempfile
from pathlib import Path
from typing import List, Optional, Dict, Any
import instaloader
from urllib.parse import urlparse
import re
import os

from ...application.interfaces.downloader_service import DownloaderService
from ...domain.entities.download_request import DownloadRequest
from ...shared.exceptions import DownloadError, UnsupportedUrlError, RateLimitError
from ...shared.config.settings import Settings

logger = logging.getLogger(__name__)


class InstagramDownloaderService(DownloaderService):
    """Instagram media downloader service using instaloader"""
    
    def __init__(self):
        self.session_file = Path(Settings.INSTAGRAM_SESSION_FILE)
        self._loader = None
        self._session_lock = asyncio.Lock()
    
    async def _get_loader(self) -> instaloader.Instaloader:
        """Get configured instaloader instance"""
        if self._loader is None:
            async with self._session_lock:
                if self._loader is None:
                    # Configure instaloader
                    self._loader = instaloader.Instaloader(
                        dirname_pattern=str(Settings.TEMP_DIR / "{target}"),
                        filename_pattern="{date_utc:%Y%m%d_%H%M%S}_{shortcode}",
                        download_video_thumbnails=False,
                        download_geotags=False,
                        download_comments=False,
                        save_metadata=False,
                        compress_json=False,
                        max_connection_attempts=3,
                        request_timeout=Settings.TIMEOUT_SECONDS,
                        sleep=True,
                        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                    )
                    
                    # Try to load session if available
                    await self._load_session()
        
        return self._loader
    
    async def _load_session(self):
        """Load Instagram session if available"""
        try:
            if self.session_file.exists() and Settings.INSTAGRAM_USERNAME:
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(
                    None,
                    lambda: self._loader.load_session_from_file(
                        Settings.INSTAGRAM_USERNAME,
                        str(self.session_file)
                    )
                )
                logger.info("Instagram session loaded successfully")
        except Exception as e:
            logger.warning(f"Failed to load Instagram session: {e}")
    
    async def can_handle(self, url: str) -> bool:
        """Check if service can handle the given URL"""
        instagram_patterns = [
            r'https?://(?:www\.)?instagram\.com/p/[\w-]+',
            r'https?://(?:www\.)?instagram\.com/reel/[\w-]+',
            r'https?://(?:www\.)?instagram\.com/tv/[\w-]+',
            r'https?://(?:www\.)?instagram\.com/stories/[\w.-]+/\d+',
            r'https?://(?:www\.)?instagr\.am/p/[\w-]+',
        ]
        
        return any(re.match(pattern, url) for pattern in instagram_patterns)
    
    def _extract_shortcode(self, url: str) -> Optional[str]:
        """Extract Instagram shortcode from URL"""
        patterns = [
            r'/p/([A-Za-z0-9_-]+)',
            r'/reel/([A-Za-z0-9_-]+)',
            r'/tv/([A-Za-z0-9_-]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        return None
    
    async def extract_media_info(self, url: str) -> Dict[str, Any]:
        """Extract media information from URL without downloading"""
        try:
            if not await self.can_handle(url):
                raise UnsupportedUrlError(f"URL not supported: {url}")
            
            shortcode = self._extract_shortcode(url)
            if not shortcode:
                raise UnsupportedUrlError(f"Could not extract shortcode from URL: {url}")
            
            loader = await self._get_loader()
            
            # Use executor to run blocking instaloader operations
            loop = asyncio.get_event_loop()
            post = await loop.run_in_executor(
                None,
                instaloader.Post.from_shortcode,
                loader.context,
                shortcode
            )
            
            media_info = {
                "shortcode": post.shortcode,
                "caption": post.caption[:500] if post.caption else None,
                "media_count": post.mediacount,
                "is_video": post.is_video,
                "video_duration": post.video_duration if post.is_video else None,
                "owner": post.owner_username,
                "likes": post.likes,
                "comments": post.comments,
                "date": post.date_utc.isoformat(),
                "typename": post.typename,
                "url": url
            }
            
            return media_info
            
        except instaloader.exceptions.InstaloaderException as e:
            if "Login required" in str(e) or "Private account" in str(e):
                raise DownloadError(f"Instagram content requires login or is private: {e}")
            elif "Rate limit" in str(e) or "429" in str(e):
                raise RateLimitError(f"Instagram rate limit exceeded: {e}")
            else:
                raise DownloadError(f"Instagram API error: {e}")
        except Exception as e:
            logger.error(f"Error extracting Instagram media info: {e}")
            raise DownloadError(f"Failed to extract media info: {e}")
    
    async def download_media(self, request: DownloadRequest) -> List[str]:
        """Download media from Instagram URL"""
        try:
            shortcode = self._extract_shortcode(request.url)
            if not shortcode:
                raise UnsupportedUrlError(f"Could not extract shortcode from URL: {request.url}")
            
            loader = await self._get_loader()
            temp_dir = Settings.TEMP_DIR / f"instagram_{request.id}"
            temp_dir.mkdir(exist_ok=True)
            
            # Configure download directory
            loader.dirname_pattern = str(temp_dir / "{target}")
            
            # Download the post
            loop = asyncio.get_event_loop()
            post = await loop.run_in_executor(
                None,
                instaloader.Post.from_shortcode,
                loader.context,
                shortcode
            )
            
            # Check file size before download
            if hasattr(post, 'video_url') and post.is_video:
                # For videos, we'll estimate or check after download
                pass
            
            # Download the post
            await loop.run_in_executor(
                None,
                loader.download_post,
                post,
                target=shortcode
            )
            
            # Find downloaded files
            downloaded_files = []
            target_dir = temp_dir / shortcode
            
            if target_dir.exists():
                for file_path in target_dir.rglob("*"):
                    if file_path.is_file() and file_path.suffix.lower() in ['.jpg', '.jpeg', '.png', '.mp4', '.mov']:
                        # Check file size
                        file_size = file_path.stat().st_size
                        max_size = Settings.MAX_FILE_SIZE * 1024 * 1024  # Convert MB to bytes
                        
                        if file_size <= max_size:
                            downloaded_files.append(str(file_path))
                        else:
                            logger.warning(f"File {file_path} exceeds size limit: {file_size} bytes")
            
            if not downloaded_files:
                raise DownloadError("No media files were downloaded or all files exceed size limit")
            
            logger.info(f"Downloaded {len(downloaded_files)} files from Instagram")
            return downloaded_files
            
        except instaloader.exceptions.InstaloaderException as e:
            if "Login required" in str(e) or "Private account" in str(e):
                raise DownloadError(f"Instagram content requires login or is private: {e}")
            elif "Rate limit" in str(e) or "429" in str(e):
                raise RateLimitError(f"Instagram rate limit exceeded: {e}")
            else:
                raise DownloadError(f"Instagram download error: {e}")
        except Exception as e:
            logger.error(f"Error downloading Instagram media: {e}")
            raise DownloadError(f"Failed to download media: {e}")
    
    async def get_media_metadata(self, url: str) -> Optional[Dict[str, Any]]:
        """Get metadata for media at URL"""
        try:
            return await self.extract_media_info(url)
        except Exception as e:
            logger.error(f"Error getting Instagram metadata: {e}")
            return None
    
    async def validate_url(self, url: str) -> bool:
        """Validate if URL is accessible and contains media"""
        try:
            await self.extract_media_info(url)
            return True
        except Exception:
            return False
    
    def get_supported_platforms(self) -> List[str]:
        """Get list of supported platforms"""
        return ["instagram"]
    
    async def cleanup_temp_files(self, file_paths: List[str]) -> None:
        """Clean up temporary files"""
        try:
            for file_path in file_paths:
                path = Path(file_path)
                if path.exists():
                    # Remove file
                    path.unlink()
                    
                    # Try to remove parent directory if empty
                    try:
                        parent = path.parent
                        if parent.exists() and not any(parent.iterdir()):
                            parent.rmdir()
                            
                            # Try to remove grandparent if empty
                            grandparent = parent.parent
                            if grandparent.exists() and grandparent != Settings.TEMP_DIR:
                                if not any(grandparent.iterdir()):
                                    grandparent.rmdir()
                    except Exception:
                        pass  # Ignore cleanup errors for directories
                        
            logger.debug(f"Cleaned up {len(file_paths)} temporary files")
        except Exception as e:
            logger.error(f"Error cleaning up temporary files: {e}") 