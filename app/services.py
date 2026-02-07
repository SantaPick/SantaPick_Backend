"""
비즈니스 로직 및 세션 관리
"""
import uuid
from typing import Dict, Any
from .models import UserInfoRequest

# 메모리 기반 세션 저장소
sessions: Dict[str, Dict[str, Any]] = {}

class UserService:
    def save_info(self, user_data: UserInfoRequest) -> Dict[str, Any]:
        session_id = str(uuid.uuid4())
        sessions[session_id] = {
            'user_info': user_data.dict(),
            'answers': [],
            'personality_scores': {},
            'created_at': None
        }
        return {
            "success": True,
            "data": {
                "session_id": session_id,
                "message": "사용자 정보가 저장되었습니다."
            }
        }

class TestService:
    def get_questions(self) -> Dict[str, Any]:
        # 데이터 로더에서 질문 가져오기
        import sys
        from pathlib import Path
        sys.path.append(str(Path(__file__).parent.parent))
        from utils.engines.data_loader import PsychologyDataLoader
        loader = PsychologyDataLoader()
        loader.load_all_data()
        
        # Trait 질문만 사용
        all_questions = []
        if loader.trait_questions is not None:
            all_questions.extend(loader.trait_questions.to_dict('records'))
            
        return {
            "success": True,
            "data": {
                "total_questions": len(all_questions),
                "questions": all_questions
            }
        }
    
    def submit(self, data) -> Dict[str, Any]:
        if data.session_id not in sessions:
            return {
                "success": False,
                "error": {"code": "SESSION_NOT_FOUND", "message": "세션을 찾을 수 없습니다."}
            }
        
        session = sessions[data.session_id]
        session['answers'].extend(data.answers)
        
        # 점수 계산
        try:
            import sys
            from pathlib import Path
            sys.path.append(str(Path(__file__).parent.parent))
            from utils.engines.scoring_calculator import ScoringCalculator
            
            calculator = ScoringCalculator()
            # 답변 형식을 scoring_calculator에 맞게 변환
            formatted_answers = {}
            for i, answer in enumerate(session['answers']):
                formatted_answers[str(i)] = answer
            
            user_weights = calculator.calculate_user_weights(formatted_answers)
            session['personality_scores'] = user_weights
            
        except Exception as e:
            # 점수 계산 실패 시 기본값 사용
            user_weights = {}
        
        if data.progress.is_final:
            return {
                "success": True,
                "data": {
                    "personality_type": "감성적인 로맨티스트",
                    "traits": user_weights,
                    "is_final": True
                }
            }
        else:
            completion_rate = (data.progress.current_step / data.progress.total_steps) * 100
            return {
                "success": True,
                "data": {
                    "progress_result": "현재까지 감성적 성향이 강해요",
                    "completion_rate": completion_rate
                }
            }

class RecommendationService:
    def __init__(self):
        self.engine = None
        
    def _get_engine(self):
        """추천 엔진 lazy loading"""
        if self.engine is None:
            import sys
            from pathlib import Path
            sys.path.append(str(Path(__file__).parent.parent))
            from utils.engines.recommendation_engine import RecommendationEngine
            self.engine = RecommendationEngine()
            self.engine.load_model()
        return self.engine
    
    def _extract_product_id(self, item_id):
        """item_id에서 실제 product_id 추출"""
        if item_id and str(item_id).isdigit():
            return int(item_id)
        return None
    
    def get_recommendations(self, session_id: str) -> Dict[str, Any]:
        if session_id not in sessions:
            return {
                "success": False,
                "error": {"code": "SESSION_NOT_FOUND", "message": "세션을 찾을 수 없습니다."}
            }
        
        session = sessions[session_id]
        user_weights = session.get('personality_scores', {})
        
        if not user_weights:
            return {
                "success": False,
                "error": {"code": "NO_PERSONALITY_DATA", "message": "성격 분석 데이터가 없습니다."}
            }
        
        try:
            # 추천 엔진 실행
            engine = self._get_engine()
            # 1. User 노드를 그래프에 추가
            user_id = engine.add_user_node(user_weights)
            # 2. 추천 생성
            recommendations = engine.get_recommendations(user_id, top_k=10)
            
            # 결과 포맷팅
            formatted_recommendations = []
            for i, rec in enumerate(recommendations):
                # recommendation_engine에서 반환하는 딕셔너리 형태 처리
                product_id = self._extract_product_id(rec.get('item_id'))
                formatted_recommendations.append({
                    "product_id": product_id,
                    "score": float(rec.get('similarity', 0)),
                    "rank": i + 1
                })
            
            return {
                "success": True,
                "data": {"recommendations": formatted_recommendations}
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": {"code": "RECOMMENDATION_ERROR", "message": f"추천 생성 실패: {str(e)}"}
            }

class ProductService:
    def __init__(self):
        self.products_df = None
        
    def _load_products(self):
        """상품 데이터 lazy loading"""
        if self.products_df is None:
            import pandas as pd
            from pathlib import Path
            products_path = Path(__file__).parent.parent / "data" / "products" / "products.csv"
            self.products_df = pd.read_csv(products_path)
        return self.products_df
    
    def get_product(self, product_id: str) -> Dict[str, Any]:
        try:
            # 상품 ID를 정수로 변환 시도
            product_id_int = int(product_id)
        except ValueError:
            return {
                "success": False,
                "error": {"code": "INVALID_PRODUCT_ID", "message": "잘못된 상품 ID입니다."}
            }
        
        products_df = self._load_products()
        product = products_df[products_df['product_id'] == product_id_int]
        
        if product.empty:
            return {
                "success": False,
                "error": {"code": "PRODUCT_NOT_FOUND", "message": "상품을 찾을 수 없습니다."}
            }
        
        # 상품 데이터 정리
        product_data = product.iloc[0].to_dict()
        
        # NaN 값을 None으로 변환
        import pandas as pd
        for key, value in product_data.items():
            if pd.isna(value):
                product_data[key] = None
        
        return {
            "success": True,
            "data": product_data
        }

# 서비스 인스턴스 생성
user_service = UserService()
test_service = TestService()
recommendation_service = RecommendationService()
product_service = ProductService()