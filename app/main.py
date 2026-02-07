"""
SantaPick Backend - FastAPI 메인 애플리케이션
"""
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

# API 라우터들 import
from .api import user, test, recommendation, products

# FastAPI 앱 생성
app = FastAPI(
    title="SantaPick API",
    description="심리테스트 기반 선물 추천 시스템",
    version="1.0.0"
)

# CORS 설정 (프론트엔드 연동용)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 개발용, 실제 배포시에는 특정 도메인만 허용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API 라우터 등록
app.include_router(user.router, tags=["사용자"])
app.include_router(test.router, tags=["심리테스트"])
app.include_router(recommendation.router, tags=["추천"])
app.include_router(products.router, tags=["상품"])

# 정적 파일 서빙 (상품 이미지)
from pathlib import Path
static_dir = Path(__file__).parent.parent / "statics"
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# 기본 엔드포인트
@app.get("/")
async def root():
    return {"message": "SantaPick API Server", "status": "running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)