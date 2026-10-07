from fastapi import HTTPException, status


class NotFound(HTTPException):
    def __init__(self, what: str):
        super().__init__(status.HTTP_404_NOT_FOUND, f"{what} not found")


class Conflict(HTTPException):
    def __init__(self, detail: str):
        super().__init__(status.HTTP_409_CONFLICT, detail)


class BadRequest(HTTPException):
    def __init__(self, detail: str):
        super().__init__(status.HTTP_400_BAD_REQUEST, detail)


class Unauthorized(HTTPException):
    def __init__(self, message: str = "Invalid username or password"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=message,
        )