import asyncio
import logging
import sys
from pathlib import Path

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from shared.config.settings import Settings
from shared.exceptions import MultisaveXException
from infrastructure.container import Container
from presentation.telegram.bot_manager import BotManager
from presentation.web.app import create_app


def setup_logging():
    """Setup application logging"""
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level=getattr(logging, Settings.LOG_LEVEL),
        handlers=[
            logging.FileHandler(Settings.LOG_FILE),
            logging.StreamHandler()
        ]
    )


async def main():
    """Main application entry point"""
    try:
        # Setup logging
        setup_logging()
        logger = logging.getLogger(__name__)
        
        logger.info("Starting MultisaveX application...")
        
        # Validate required settings
        Settings.validate_required_settings()
        
        # Setup directories
        Settings.setup_directories()
        
        # Create dependency injection container
        container = Container()
        
        # Create bot manager
        bot_manager = BotManager(container)
        
        # Create web app
        web_app = create_app(container)
        
        # Start the application
        await bot_manager.start()
        
        logger.info("Application started successfully")
        
        # Keep the application running
        await asyncio.Future()
        
    except MultisaveXException as e:
        logger.error(f"Application error: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Application stopped by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)
    finally:
        # Cleanup
        if 'bot_manager' in locals():
            await bot_manager.stop()
        logger.info("Application stopped")


if __name__ == "__main__":
    asyncio.run(main())