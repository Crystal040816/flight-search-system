# backend/app/models/response.py
from typing import Any, Optional, List, Dict, Union
from dataclasses import dataclass, field


@dataclass
class UnifiedResponse:
    """统一响应格式"""
    code: int
    message: str
    data: Optional[Any] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "code": self.code,
            "message": self.message,
            "data": self.data
        }

    @staticmethod
    def success(data: Any = None, message: str = "success") -> Dict[str, Any]:
        return {
            "code": 200,
            "message": message,
            "data": data
        }

    @staticmethod
    def error(message: str = "error", code: int = 500, data: Any = None) -> Dict[str, Any]:
        return {
            "code": code,
            "message": message,
            "data": data
        }

    @staticmethod
    def bad_request(message: str = "参数错误", data: Any = None) -> Dict[str, Any]:
        return {
            "code": 400,
            "message": message,
            "data": data
        }