from fastapi import APIRouter, HTTPException
from app.models import *
from app.services import IntermediateService

router = APIRouter(prefix="/api/intermediate", tags=["intermediate"])

@router.get("/{session_id}")
async def get_intermediate_result(session_id: str):
    """
    중간 결과 조회 - GPT 기반 성격 분석
    """
    try:
        service = IntermediateService()
        result = service.get_intermediate_result(session_id)
        
        if not result["success"]:
            raise HTTPException(status_code=404, detail=result["error"])
            
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"중간 결과 생성 중 오류가 발생했습니다: {str(e)}")