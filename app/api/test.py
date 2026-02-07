"""
심리테스트 관련 API
"""
from fastapi import APIRouter
from ..models import TestQuestionsResponse, TestSubmitRequest, TestSubmitResponse
from ..services import test_service

router = APIRouter()

@router.get("/api/test/questions", response_model=TestQuestionsResponse)
async def get_test_questions():
    """심리테스트 문항 조회"""
    return test_service.get_questions()

@router.post("/api/test/submit", response_model=TestSubmitResponse)
async def submit_test_answers(data: TestSubmitRequest):
    """심리테스트 답변 제출"""
    return test_service.submit(data)