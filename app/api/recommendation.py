"""
추천 관련 API
"""
from fastapi import APIRouter
from ..models import RecommendationResponse
from ..services import recommendation_service

router = APIRouter()

@router.get("/api/recommendation/{session_id}", response_model=RecommendationResponse)
async def get_recommendations(session_id: str):
    """그래프 기반 추천 상품 조회"""
    return recommendation_service.get_recommendations(session_id)