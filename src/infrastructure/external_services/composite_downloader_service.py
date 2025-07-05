import asyncio
import logging
from typing import List, Optional, Dict, Any

from ...application.interfaces.downloader_service import DownloaderService
from ...domain.entities.download_request import DownloadRequest
from ...shared.exceptions import DownloadError, UnsupportedUrlError

logger = logging.getLogger(__name__)


class CompositeDownloaderService(DownloaderService):
    """Composite downloader service that delegates to platform-specific services"""
    
    def __init__(self, downloaders: List[DownloaderService]):
        self.downloaders = downloaders
        logger.info(f"Initialized composite downloader with {len(downloaders)} services")
    
    async def can_handle(self, url: str) -> bool:
        """Check if any service can handle the given URL"""
        for downloader in self.downloaders:
            if await downloader.can_handle(url):
                return True
        return False
    
    async def _get_handler(self, url: str) -> Optional[DownloaderService]:
        """Get the appropriate downloader service for URL"""
        for downloader in self.downloaders:
            if await downloader.can_handle(url):
                return downloader
        return None
    
    async def extract_media_info(self, url: str) -> Dict[str, Any]:
        """Extract media information from URL without downloading"""
        handler = await self._get_handler(url)
        if not handler:
            raise UnsupportedUrlError(f"No handler found for URL: {url}")
        
        logger.debug(f"Using {handler.__class__.__name__} for info extraction")
        return await handler.extract_media_info(url)
    
    async def download_media(self, request: DownloadRequest) -> List[str]:
        """Download media from URL using appropriate service"""
        handler = await self._get_handler(request.url)
        if not handler:
            raise UnsupportedUrlError(f"No handler found for URL: {request.url}")
        
        logger.info(f"Using {handler.__class__.__name__} for download")
        return await handler.download_media(request)
    
    async def get_media_metadata(self, url: str) -> Optional[Dict[str, Any]]:
        """Get metadata for media at URL"""
        handler = await self._get_handler(url)
        if not handler:
            logger.warning(f"No handler found for URL: {url}")
            return None
        
        return await handler.get_media_metadata(url)
    
    async def validate_url(self, url: str) -> bool:
        """Validate if URL is accessible and contains media"""
        handler = await self._get_handler(url)
        if not handler:
            return False
        
        return await handler.validate_url(url)
    
    def get_supported_platforms(self) -> List[str]:
        """Get list of all supported platforms"""
        platforms = []
        for downloader in self.downloaders:
            platforms.extend(downloader.get_supported_platforms())
        return list(set(platforms))  # Remove duplicates
    
    async def cleanup_temp_files(self, file_paths: List[str]) -> None:
        """Clean up temporary files using all available services"""
        cleanup_tasks = []
        for downloader in self.downloaders:
            cleanup_tasks.append(downloader.cleanup_temp_files(file_paths))
        
        # Run all cleanup operations concurrently
        try:
            await asyncio.gather(*cleanup_tasks, return_exceptions=True)
        except Exception as e:
            logger.error(f"Error during composite cleanup: {e}")
    
    def add_downloader(self, downloader: DownloaderService):
        """Add a new downloader service"""
        self.downloaders.append(downloader)
        logger.info(f"Added {downloader.__class__.__name__} to composite service")
    
    def remove_downloader(self, downloader_class: type):
        """Remove downloader service by class"""
        self.downloaders = [d for d in self.downloaders if not isinstance(d, downloader_class)]
        logger.info(f"Removed {downloader_class.__name__} from composite service")
    
    def get_downloader_count(self) -> int:
        """Get number of registered downloaders"""
        return len(self.downloaders)
    
    async def get_platform_for_url(self, url: str) -> Optional[str]:
        """Get platform name for URL"""
        handler = await self._get_handler(url)
        if not handler:
            return None
        
        platforms = handler.get_supported_platforms()
        return platforms[0] if platforms else None 