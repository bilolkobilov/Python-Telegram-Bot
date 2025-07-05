from typing import Optional
from .base import MultisaveXException


class RateLimitError(MultisaveXException):
    """Exception raised when rate limit is exceeded"""
    
    def __init__(self, action: str, reset_time: Optional[int] = None):
        message = f"Rate limit exceeded for action: {action}"
        if reset_time:
            message += f". Reset in {reset_time} seconds"
        
        super().__init__(message, "RATE_LIMIT_EXCEEDED")
        self.action = action
        self.reset_time = reset_time
        self.details["action"] = action
        if reset_time:
            self.details["reset_time"] = reset_time