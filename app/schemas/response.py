from typing import Any, Optional, Generic, TypeVar
from pydantic import BaseModel

T = TypeVar("T")

class ApiResponse(BaseModel, Generic[T]):
    success: bool
    code: int
    message: str
    data: Optional[T] = None

    @classmethod
    def ok(cls, data: Any = None, message: str = "Success", code: int = 200):
        return cls(success=True, code=code, message=message, data=data)

    @classmethod
    def error(cls, message: str = "Error", code: int = 400, data: Any = None):
        return cls(success=False, code=code, message=message, data=data)
