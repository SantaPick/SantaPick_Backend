"""
상품 관련 API
"""
from fastapi import APIRouter
from ..models import ProductResponse
from ..services import product_service

router = APIRouter()

@router.get("/api/products/{product_id}", response_model=ProductResponse)
async def get_product_detail(product_id: str):
    """상품 상세 정보 조회"""
    return product_service.get_product(product_id)