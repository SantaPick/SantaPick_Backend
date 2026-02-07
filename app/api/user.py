"""
사용자 관련 API
"""
from fastapi import APIRouter
from ..models import UserInfoRequest, UserInfoResponse
from ..services import user_service

router = APIRouter()

@router.post("/api/user/info", response_model=UserInfoResponse)
async def save_user_info(user_data: UserInfoRequest):
    """사용자 기본정보 저장"""
    return user_service.save_info(user_data)