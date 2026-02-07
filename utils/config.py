"""
프로젝트 전역 설정 파일
"""

import os
from pathlib import Path

# 프로젝트 루트 경로 (SantaPick_Backend)
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
UTILS_DIR = PROJECT_ROOT / "utils"
GRAPH_DATA_DIR = UTILS_DIR / "graph_data"

# 그래프 관련 경로
GRAPH_PKL_PATH = UTILS_DIR / "models" / "recommendation_graph.pkl"
EMBEDDINGS_PKL_PATH = UTILS_DIR / "models" / "embeddings.pkl"
ENTITY_LIST_PATH = GRAPH_DATA_DIR / "entity_list.txt"
TRAIT_CONCEPT_WEIGHTS_PATH = GRAPH_DATA_DIR / "trait_concept_weights.txt"
ITEM_CONCEPT_WEIGHTS_PATH = GRAPH_DATA_DIR / "item_concept_weights.txt"

# 심리테스트 관련
SURVEY_QUESTIONS_PATH = DATA_DIR / "survey_questions.json"

# 모델 하이퍼파라미터
MODEL_CONFIG = {
    "embedding_dim": 128,
    "hidden_dims": [256, 128],
    "learning_rate": 0.001,
    "batch_size": 512,
    "epochs": 100,
    "dropout": 0.2,
    "weight_decay": 1e-5
}

# 추천 설정
RECOMMENDATION_CONFIG = {
    "top_k": 10,  # Top-K 추천 개수
    "similarity_threshold": 0.1,  # 유사도 임계값
    "user_id_start": 2000  # User 노드 ID 시작 번호
}

# 심리테스트 척도 매핑
PSYCHOLOGY_TRAITS = {
    "Openness": "개방성",
    "Conscientiousness": "성실성", 
    "Extraversion": "외향성",
    "Agreeableness": "친화성",
    "Neuroticism": "신경성"
}

# 로깅 설정
LOGGING_CONFIG = {
    "level": "INFO",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "log_file": PROJECT_ROOT / "logs" / "recommendation.log"
}

def ensure_directories():
    """필요한 디렉토리 생성"""
    directories = [
        DATA_DIR,
        MODEL_DIR, 
        GRAPH_DATA_DIR,
        PROJECT_ROOT / "logs"
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)

if __name__ == "__main__":
    ensure_directories()
    print("프로젝트 디렉토리 설정 완료")
    print(f"프로젝트 루트: {PROJECT_ROOT}")
    print(f"데이터 경로: {DATA_DIR}")