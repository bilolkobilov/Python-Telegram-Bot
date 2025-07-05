from .base import MultisaveXException


class UserNotFoundError(MultisaveXException):
    """Exception raised when user is not found"""
    
    def __init__(self, user_id: int):
        super().__init__(f"User not found: {user_id}", "USER_NOT_FOUND")
        self.user_id = user_id
        self.details["user_id"] = user_id


class UserBannedError(MultisaveXException):
    """Exception raised when user is banned"""
    
    def __init__(self, user_id: int):
        super().__init__(f"User is banned: {user_id}", "USER_BANNED")
        self.user_id = user_id
        self.details["user_id"] = user_id


class UserAlreadyExistsError(MultisaveXException):
    """Exception raised when user already exists"""
    
    def __init__(self, user_id: int):
        super().__init__(f"User already exists: {user_id}", "USER_ALREADY_EXISTS")
        self.user_id = user_id
        self.details["user_id"] = user_id


class InsufficientPermissionsError(MultisaveXException):
    """Exception raised when user has insufficient permissions"""
    
    def __init__(self, user_id: int, required_permission: str):
        super().__init__(
            f"User {user_id} has insufficient permissions for {required_permission}",
            "INSUFFICIENT_PERMISSIONS"
        )
        self.user_id = user_id
        self.required_permission = required_permission
        self.details["user_id"] = user_id
        self.details["required_permission"] = required_permission