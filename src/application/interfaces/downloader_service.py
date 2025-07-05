from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from pathlib import Path

from ...domain.entities.media import Media
from ...domain.entities.download_request import DownloadRequest


class DownloaderService(ABC):
    """Abstract downloader service interface"""
    
    @abstractmethod
    async def can_handle(self, url: str) -> bool:
        """Check if service can handle the given URL"""
        pass
    
    @abstractmethod
    async def extract_media_info(self, url: str) -> Dict[str, Any]:
        """Extract media information from URL without downloading"""
        pass
    
    @abstractmethod
    async def download_media(self, request: DownloadRequest) -> List[str]:
        """
        Download media from URL and return list of file paths
        
        Args:
            request: Download request containing URL and metadata
            
        Returns:
            List of downloaded file paths
            
        Raises:
            DownloadError: If download fails
            UnsupportedUrlError: If URL is not supported
            RateLimitError: If rate limit is exceeded
        """
        pass
    
    @abstractmethod
    async def get_media_metadata(self, url: str) -> Optional[Dict[str, Any]]:
        """Get metadata for media at URL"""
        pass
    
    @abstractmethod
    async def validate_url(self, url: str) -> bool:
        """Validate if URL is accessible and contains media"""
        pass
    
    @abstractmethod
    def get_supported_platforms(self) -> List[str]:
        """Get list of supported platforms"""
        pass
    
    @abstractmethod
    async def cleanup_temp_files(self, file_paths: List[str]) -> None:
        """Clean up temporary files"""
        pass