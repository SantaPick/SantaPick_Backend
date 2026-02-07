# SantaPick Backend

심리테스트 기반 선물 추천 시스템의 백엔드 API 서버

## 프로젝트 구조

```
SantaPick_Backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI 앱 진입점
│   ├── models.py               # Pydantic 모델 정의
│   ├── services.py             # 비즈니스 로직 및 세션 관리
│   └── api/                    # API 라우터
│       ├── __init__.py
│       ├── user.py            # 사용자 정보 API
│       ├── test.py            # 심리테스트 API
│       ├── recommendation.py  # 추천 API
│       └── products.py        # 상품 API
├── utils/
│   ├── __init__.py
│   ├── config.py              # 프로젝트 설정
│   ├── engines/               # 추천 엔진 및 데이터 처리
│   │   ├── __init__.py
│   │   ├── data_loader.py     # 심리테스트 질문 로더
│   │   ├── scoring_calculator.py  # 성격 점수 계산
│   │   └── recommendation_engine.py  # Node2Vec 추천 엔진
│   ├── models/                # 학습된 모델 파일
│   │   ├── embeddings.pkl
│   │   └── recommendation_graph.pkl
│   └── graph_data/            # 그래프 데이터
│       └── entity_list.txt
├── data/
│   ├── products/              # 상품 데이터
│   │   └── products.csv
│   └── psychology-question/   # 심리테스트 질문
│       └── trait-question.csv
├── statics/                   # 정적 파일 (이미지 등)
├── requirements.txt           # Python 의존성
├── API_SPECIFICATION.md       # API 명세서
└── README.md
```

## 기술 스택

- **Framework**: FastAPI 0.104.1
- **서버**: Uvicorn
- **데이터 처리**: Pandas, NumPy
- **머신러닝**: scikit-learn, NetworkX
- **데이터 검증**: Pydantic
- **세션 관리**: 메모리 기반 (in-memory dictionary)

## 주요 기능

1. **사용자 세션 관리**: UUID 기반 세션 ID 생성 및 관리
2. **심리테스트**: 44개 Trait 질문 처리 및 Big Five 성격 분석
3. **추천 시스템**: Node2Vec 기반 그래프 임베딩을 활용한 개인화 추천
4. **상품 조회**: 상품 상세 정보 제공
5. **정적 파일 서빙**: 상품 이미지 등 정적 파일 제공

## 설치 및 실행

### 1. 환경 설정

Conda 환경을 사용하는 경우:

```bash
# Conda 환경 생성 (이미 생성되어 있다면 생략)
conda create -n santapick-backend python=3.10
conda activate santapick-backend
```

또는 Python venv 사용:

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows
```

### 2. 의존성 설치

```bash
cd /home/yongbin53/kyb/SantaPick/SantaPick_Backend
pip install -r requirements.txt
```

### 3. 데이터 파일 확인

다음 파일들이 존재하는지 확인:

- `utils/models/embeddings.pkl` - 노드 임베딩 모델
- `utils/models/recommendation_graph.pkl` - 추천 그래프
- `data/products/products.csv` - 상품 데이터
- `data/psychology-question/trait-question.csv` - 심리테스트 질문 (44개)

### 4. 서버 실행

```bash
# Conda 환경 활성화 (필요한 경우)
conda activate santapick-backend

# 서버 실행
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

서버가 실행되면 다음 URL에서 접근 가능:

- API 서버: http://localhost:8000
- Swagger UI (API 문서): http://localhost:8000/docs
- ReDoc (API 문서): http://localhost:8000/redoc
- 헬스 체크: http://localhost:8000/health

## API 엔드포인트

### 사용자 관리
- `POST /api/user/info` - 사용자 기본정보 저장

### 심리테스트
- `GET /api/test/questions` - 심리테스트 문항 조회 (44개)
- `POST /api/test/submit` - 심리테스트 답변 제출

### 추천 시스템
- `GET /api/recommendation/{session_id}` - 추천 상품 조회 (Top 10)

### 상품
- `GET /api/products/{product_id}` - 상품 상세 정보

### 정적 파일
- `GET /static/*` - 정적 파일 서빙

자세한 API 명세는 `API_SPECIFICATION.md`를 참고하세요.

## 데이터 플로우

1. **사용자 정보 입력**: Landing Page에서 사용자 정보 입력 → `POST /api/user/info` → session_id 생성
2. **심리테스트 진행**: 질문 조회 → 답변 제출 (중간점검/최종완료) → 성격 점수 계산
3. **추천 생성**: 성격 점수를 기반으로 Node2Vec 그래프 알고리즘으로 Top 10 상품 추천
4. **상품 조회**: 추천된 상품의 상세 정보 조회

## 세션 관리

- **방식**: 메모리 기반 세션 저장소 (in-memory dictionary)
- **세션 ID**: UUID v4 형식
- **저장 데이터**: 
  - 사용자 정보 (user_info)
  - 답변 배열 (answers)
  - 성격 점수 (personality_scores)
- **주의사항**: 서버 재시작 시 모든 세션 데이터가 초기화됩니다.

## 성능

- 첫 번째 추천: 약 0.86초 (모델 로딩 포함)
- 이후 추천: 평균 0.12초
- 추천 개수: Top 10개 상품

## 개발 환경

- Python 3.10+
- FastAPI 0.104.1
- Uvicorn 0.24.0

## 의존성

주요 의존성 패키지:

```
fastapi==0.104.1
uvicorn[standard]==0.24.0
pandas==2.1.3
numpy==1.24.3
scikit-learn==1.3.2
networkx==3.2.1
python-multipart==0.0.6
python-dotenv==1.0.0
```

전체 목록은 `requirements.txt`를 참고하세요.

## 문제 해결

### 모듈 import 오류
- `conda activate santapick-backend`로 가상환경이 활성화되어 있는지 확인
- `pip install -r requirements.txt`로 의존성이 설치되어 있는지 확인

### 모델 파일 없음 오류
- `utils/models/` 디렉토리에 `embeddings.pkl`과 `recommendation_graph.pkl` 파일이 있는지 확인
- `Present-Recommendation` 프로젝트에서 모델 파일을 복사했는지 확인

### 데이터 파일 없음 오류
- `data/products/products.csv` 파일이 있는지 확인
- `data/psychology-question/trait-question.csv` 파일이 있는지 확인

## 라이선스

LICENSE 파일을 참고하세요.
