import asyncio
import logging
import tempfile
from pathlib import Path
from typing import List, Optional, Dict, Any
import yt_dlp
from urllib.parse import urlparse
import re
import os
import json

from ...application.interfaces.downloader_service import DownloaderService
from ...domain.entities.download_request import DownloadRequest
from ...shared.exceptions import DownloadError, UnsupportedUrlError, RateLimitError
from ...shared.config.settings import Settings

logger = logging.getLogger(__name__)


class TikTokDownloaderService(DownloaderService):
    """TikTok media downloader service using yt-dlp"""
    
    def __init__(self):
        self.temp_dir = Settings.TEMP_DIR
        self._ydl_opts = self._get_ydl_options()
    
    def _get_ydl_options(self) -> Dict[str, Any]:
        """Get yt-dlp options"""
        return {
            'format': 'best[ext=mp4]/best',
            'outtmpl': str(self.temp_dir / 'tiktok_%(id)s.%(ext)s'),
            'writeinfojson': False,
            'writesubtitles': False,
            'writeautomaticsub': False,
            'embed_subs': False,
            'extractaudio': False,
            'ignoreerrors': False,
            'no_warnings': True,
            'quiet': True,
            'verbose': False,
            'socket_timeout': Settings.TIMEOUT_SECONDS,
            'retries': Settings.MAX_RETRIES,
            'fragment_retries': Settings.MAX_RETRIES,
            'http_chunk_size': 10485760,  # 10MB
            'prefer_insecure': False,
            'cookiefile': None,
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'headers': {
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-us,en;q=0.5',
                'Sec-Fetch-Mode': 'navigate',
            }
        }
    
    async def can_handle(self, url: str) -> bool:
        """Check if service can handle the given URL"""
        tiktok_patterns = [
            r'https?://(?:www\.)?tiktok\.com/@[\w.-]+/video/\d+',
            r'https?://(?:vm\.|vt\.)?tiktok\.com/[\w.-]+',
            r'https?://(?:www\.)?tiktok\.com/t/[\w.-]+',
            r'https?://m\.tiktok\.com/v/\d+',
        ]
        
        return any(re.match(pattern, url) for pattern in tiktok_patterns)
    
    async def extract_media_info(self, url: str) -> Dict[str, Any]:
        """Extract media information from URL without downloading"""
        try:
            if not await self.can_handle(url):
                raise UnsupportedUrlError(f"URL not supported: {url}")
            
            # Configure yt-dlp for info extraction only
            info_opts = self._ydl_opts.copy()
            info_opts.update({
                'skip_download': True,
                'quiet': True,
                'no_warnings': True
            })
            
            loop = asyncio.get_event_loop()
            
            def extract_info():
                with yt_dlp.YoutubeDL(info_opts) as ydl:
                    return ydl.extract_info(url, download=False)
            
            info = await loop.run_in_executor(None, extract_info)
            
            if not info:
                raise DownloadError("Could not extract video information")
            
            media_info = {
                "id": info.get("id"),
                "title": info.get("title", "").strip(),
                "description": info.get("description", "").strip()[:500],
                "uploader": info.get("uploader"),
                "uploader_id": info.get("uploader_id"),
                "duration": info.get("duration"),
                "view_count": info.get("view_count"),
                "like_count": info.get("like_count"),
                "comment_count": info.get("comment_count"),
                "upload_date": info.get("upload_date"),
                "ext": info.get("ext"),
                "filesize": info.get("filesize"),
                "width": info.get("width"),
                "height": info.get("height"),
                "fps": info.get("fps"),
                "url": url,
                "webpage_url": info.get("webpage_url"),
                "thumbnail": info.get("thumbnail")
            }
            
            return media_info
            
        except yt_dlp.DownloadError as e:
            error_msg = str(e).lower()
            if "private" in error_msg or "unavailable" in error_msg:
                raise DownloadError(f"TikTok video is private or unavailable: {e}")
            elif "rate" in error_msg or "429" in error_msg:
                raise RateLimitError(f"TikTok rate limit exceeded: {e}")
            else:
                raise DownloadError(f"TikTok extraction error: {e}")
        except Exception as e:
            logger.error(f"Error extracting TikTok media info: {e}")
            raise DownloadError(f"Failed to extract media info: {e}")
    
    async def download_media(self, request: DownloadRequest) -> List[str]:
        """Download media from TikTok URL"""
        try:
            # Create unique temp directory for this request
            temp_dir = self.temp_dir / f"tiktok_{request.id}"
            temp_dir.mkdir(exist_ok=True)
            
            # Configure download options
            download_opts = self._ydl_opts.copy()
            download_opts.update({
                'outtmpl': str(temp_dir / 'tiktok_%(id)s.%(ext)s'),
                'max_filesize': Settings.MAX_FILE_SIZE * 1024 * 1024,  # Convert MB to bytes
            })
            
            loop = asyncio.get_event_loop()
            downloaded_files = []
            
            def download():
                with yt_dlp.YoutubeDL(download_opts) as ydl:
                    # Get info first to check file size
                    info = ydl.extract_info(request.url, download=False)
                    
                    if info and info.get('filesize'):
                        filesize = info['filesize']
                        max_size = Settings.MAX_FILE_SIZE * 1024 * 1024
                        if filesize > max_size:
                            raise DownloadError(f"File size ({filesize} bytes) exceeds limit ({max_size} bytes)")
                    
                    # Download the video
                    ydl.download([request.url])
                    
                    # Find downloaded files
                    files = []
                    for file_path in temp_dir.glob("*"):
                        if file_path.is_file() and file_path.suffix.lower() in ['.mp4', '.webm', '.mkv', '.mov']:
                            # Double-check file size
                            file_size = file_path.stat().st_size
                            max_size = Settings.MAX_FILE_SIZE * 1024 * 1024
                            
                            if file_size <= max_size:
                                files.append(str(file_path))
                            else:
                                logger.warning(f"Downloaded file {file_path} exceeds size limit: {file_size} bytes")
                                file_path.unlink()  # Remove oversized file
                    
                    return files
            
            downloaded_files = await loop.run_in_executor(None, download)
            
            if not downloaded_files:
                raise DownloadError("No video files were downloaded or all files exceed size limit")
            
            logger.info(f"Downloaded {len(downloaded_files)} files from TikTok")
            return downloaded_files
            
        except yt_dlp.DownloadError as e:
            error_msg = str(e).lower()
            if "private" in error_msg or "unavailable" in error_msg:
                raise DownloadError(f"TikTok video is private or unavailable: {e}")
            elif "rate" in error_msg or "429" in error_msg:
                raise RateLimitError(f"TikTok rate limit exceeded: {e}")
            elif "file size" in error_msg or "too large" in error_msg:
                raise DownloadError(f"TikTok video file is too large: {e}")
            else:
                raise DownloadError(f"TikTok download error: {e}")
        except Exception as e:
            logger.error(f"Error downloading TikTok media: {e}")
            raise DownloadError(f"Failed to download media: {e}")
    
    async def get_media_metadata(self, url: str) -> Optional[Dict[str, Any]]:
        """Get metadata for media at URL"""
        try:
            return await self.extract_media_info(url)
        except Exception as e:
            logger.error(f"Error getting TikTok metadata: {e}")
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
        return ["tiktok"]
    
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
                    except Exception:
                        pass  # Ignore cleanup errors for directories
                        
            logger.debug(f"Cleaned up {len(file_paths)} temporary files")
        except Exception as e:
            logger.error(f"Error cleaning up temporary files: {e}") 