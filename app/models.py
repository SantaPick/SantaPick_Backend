"""
Pydantic 모델 정의
"""
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

# 사용자 정보 관련
class UserInfoRequest(BaseModel):
    name: str
    gender: str
    age: int
    city: str
    date: str
    time: str

class UserInfoResponse(BaseModel):
    success: bool
    data: Optional[Dict[str, str]] = None
    error: Optional[Dict[str, str]] = None

# 심리테스트 관련
class TestQuestionsResponse(BaseModel):
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, str]] = None

class TestProgress(BaseModel):
    current_step: int
    total_steps: int
    is_final: bool

class TestSubmitRequest(BaseModel):
    session_id: str
    answers: List[Dict[str, Any]]
    progress: TestProgress

class TestSubmitResponse(BaseModel):
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, str]] = None

# 추천 관련
class RecommendationItem(BaseModel):
    product_id: str
    score: float
    rank: int

class RecommendationResponse(BaseModel):
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, str]] = None

# 상품 관련
class ProductResponse(BaseModel):
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, str]] = None

# 에러 응답
class ErrorResponse(BaseModel):
    success: bool
    error: Dict[str, str]