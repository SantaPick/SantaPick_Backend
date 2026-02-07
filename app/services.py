"""
비즈니스 로직 및 세션 관리
"""
import uuid
from typing import Dict, Any
from .models import UserInfoRequest
from utils.gpt_service import GPTService

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
        structured_questions = loader.create_question_structure()
        
        return {
            "success": True,
            "data": {
                "total_questions": len(structured_questions),
                "questions": structured_questions
            }
        }
    
    def submit(self, data) -> Dict[str, Any]:
        if data.session_id not in sessions:
            return {
                "success": False,
                "data": None,
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
            # 점수 계산 실패 시 오류 반환
            print(f"점수 계산 실패: {e}")
            print(f"답변 데이터 형식: {session.get('answers', [])[:2]}")  # 처음 2개 답변 확인
            return {
                "success": False,
                "data": None,
                "error": {"code": "SCORING_ERROR", "message": f"점수 계산 실패: {str(e)}"}
            }
        
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
        self.gpt_service = GPTService()
        self.entity_mapping = None
        
    def _load_entity_mapping(self):
        """entity_list.txt에서 그래프 노드 ID → 실제 상품 ID 매핑 로드"""
        if self.entity_mapping is None:
            import pandas as pd
            from pathlib import Path
            
            # entity_list.txt 파일 경로
            entity_path = Path(__file__).parent.parent / "data" / "graph_data" / "entity_list.txt"
            
            if not entity_path.exists():
                # 원본 경로에서 복사
                original_path = Path(__file__).parent.parent.parent / "Present-Recommedation" / "data" / "graph_data" / "entity_list.txt"
                if original_path.exists():
                    entity_path.parent.mkdir(parents=True, exist_ok=True)
                    import shutil
                    shutil.copy(original_path, entity_path)
            
            self.entity_mapping = {}
            if entity_path.exists():
                with open(entity_path, 'r') as f:
                    for line in f:
                        parts = line.strip().split()
                        if len(parts) >= 3 and parts[2] == 'item':
                            real_product_id = int(parts[0])  # 실제 상품 ID
                            graph_node_id = int(parts[1])   # 그래프 노드 ID
                            self.entity_mapping[graph_node_id] = real_product_id
        
        return self.entity_mapping
        
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
        """그래프 노드 ID에서 실제 product_id 추출"""
        try:
            graph_node_id = int(item_id)
            entity_mapping = self._load_entity_mapping()
            return entity_mapping.get(graph_node_id, None)
        except (ValueError, TypeError):
            return None
    
    def get_recommendations(self, session_id: str) -> Dict[str, Any]:
        if session_id not in sessions:
            return {
                "success": False,
                "data": None,
                "error": {"code": "SESSION_NOT_FOUND", "message": "세션을 찾을 수 없습니다."}
            }
        
        session = sessions[session_id]
        user_weights = session.get('personality_scores', {})
        
        # personality_scores가 없으면 추천 불가
        if not user_weights:
            return {
                "success": False,
                "data": None,
                "error": {"code": "NO_PERSONALITY_DATA", "message": "성격 분석 결과가 없습니다. 먼저 심리테스트를 완료해주세요."}
            }
        
        # GPT 분석 결과를 기반으로 가중치 최종 조정 (선택사항)
        try:
            all_answers = session.get('answers', [])
            gpt_result = self.gpt_service.generate_final_result(
                user_weights,
                session['user_info']['name'], 
                all_answers
            )
            
            # GPT 분석 결과를 바탕으로 가중치 조정
            adjusted_weights = self._adjust_weights_with_gpt_analysis(
                user_weights, 
                gpt_result.get('personality_type', ''),
                gpt_result.get('description', '')
            )
            
            session['personality_scores'] = adjusted_weights
            print(f"GPT 조정 후 가중치 (총 {len(adjusted_weights)}개): {adjusted_weights}")
            
        except Exception as e:
            print(f"GPT 가중치 조정 실패: {e}")
            # GPT 조정 실패 시 원본 가중치 사용
            print(f"기본 계산된 사용자 가중치 (총 {len(user_weights)}개): {user_weights}")
            for trait in all_trait_nodes:
                if trait in ['Extraversion', 'Agreeableness', 'Conscientiousness']:
                    user_weights[trait] = 0.5
                elif trait == 'Openness':
                    user_weights[trait] = 0.7
                elif trait == 'Neuroticism':
                    user_weights[trait] = 0.3
                else:
                    user_weights[trait] = 0.4
        
        try:
            # 추천 엔진 실행
            engine = self._get_engine()
            # 1. User 노드를 그래프에 추가
            user_id = engine.add_user_node(user_weights)
            # 2. 추천 생성 (더 많은 후보 생성 후 다양성 필터링)
            recommendations = engine.get_recommendations(user_id, top_k=20)
            
            # 3. 다양성 기반 필터링으로 최종 10개 선택
            diverse_recommendations = self._apply_diversity_filter(recommendations, target_count=10)
            
            # 결과 포맷팅
            formatted_recommendations = []
            for i, rec in enumerate(diverse_recommendations):
                # recommendation_engine에서 반환하는 딕셔너리 형태 처리
                product_id = self._extract_product_id(rec.get('item_id'))
                formatted_recommendations.append({
                    "product_id": product_id,
                    "score": float(rec.get('similarity', 0)),
                    "rank": i + 1
                })
            
            # GPT를 통한 최종 성격 분석 추가
            try:
                user_name = session['user_info']['name']
                all_answers = session.get('answers', [])
                gpt_result = self.gpt_service.generate_final_result(user_weights, user_name, all_answers)
                
                return {
                    "success": True,
                    "data": {
                        "recommendations": formatted_recommendations,
                        "personality_analysis": {
                            "personality_type": gpt_result["personality_type"],
                            "description": gpt_result["description"]
                        },
                        "user_name": session['user_info']['name'],
                        "traits": user_weights
                    }
                }
            except Exception as gpt_error:
                print(f"GPT 최종 분석 오류: {gpt_error}")
                # GPT 오류 시에도 추천 결과는 반환
                return {
                    "success": True,
                    "data": {
                        "recommendations": formatted_recommendations,
                        "personality_analysis": {
                            "personality_type": "매력적인 개성",
                            "description": f"{session['user_info']['name']}님만의 특별한 매력이 돋보입니다."
                        },
                        "user_name": session['user_info']['name'],
                        "traits": user_weights
                    }
                }
            
        except Exception as e:
            return {
                "success": False,
                "data": None,
                "error": {"code": "RECOMMENDATION_ERROR", "message": f"추천 생성 실패: {str(e)}"}
            }
    
    def _adjust_weights_with_gpt_analysis(self, base_weights, personality_type, description):
        """GPT 분석 결과를 바탕으로 가중치 조정"""
        adjusted_weights = base_weights.copy()
        
        # 성격 유형별 가중치 조정 패턴
        adjustments = {}
        
        # 외향성 관련 조정
        if any(word in personality_type.lower() for word in ['외향', '사교', '활발', '적극']):
            adjustments['Extraversion'] = 0.2
            adjustments['Agreeableness'] = 0.1
        elif any(word in personality_type.lower() for word in ['내향', '조용', '신중', '차분']):
            adjustments['Extraversion'] = -0.2
            adjustments['Openness'] = 0.1
        
        # 창의성 관련 조정
        if any(word in personality_type.lower() for word in ['창의', '예술', '상상', '혁신']):
            adjustments['Openness'] = 0.3
            adjustments['Modern'] = 0.2
        elif any(word in personality_type.lower() for word in ['보수', '전통', '안정', '실용']):
            adjustments['Conscientiousness'] = 0.2
            adjustments['Openness'] = -0.1
        
        # 감성 관련 조정
        if any(word in personality_type.lower() for word in ['감성', '감정', '따뜻', '온화']):
            adjustments['Warm'] = 0.3
            adjustments['Cute'] = 0.2
            adjustments['Agreeableness'] = 0.1
        elif any(word in personality_type.lower() for word in ['이성', '논리', '차가', '냉정']):
            adjustments['Sharp'] = 0.2
            adjustments['Modern'] = 0.1
        
        # 완벽주의 관련 조정
        if any(word in personality_type.lower() for word in ['완벽', '꼼꼼', '체계', '정확']):
            adjustments['Conscientiousness'] = 0.3
            adjustments['Elegant'] = 0.2
        elif any(word in personality_type.lower() for word in ['자유', '즉흥', '유연', '편안']):
            adjustments['Conscientiousness'] = -0.1
            adjustments['Cute'] = 0.1
        
        # 럭셔리/고급 관련 조정
        if any(word in personality_type.lower() for word in ['고급', '세련', '우아', '품격']):
            adjustments['Luxurious'] = 0.3
            adjustments['Elegant'] = 0.2
        elif any(word in personality_type.lower() for word in ['소박', '단순', '검소', '실용']):
            adjustments['Luxurious'] = -0.2
        
        # 조정 적용
        for trait, adjustment in adjustments.items():
            if trait in adjusted_weights:
                new_value = adjusted_weights[trait] + adjustment
                adjusted_weights[trait] = max(0.0, min(1.0, new_value))  # 0-1 범위로 클리핑
        
        # 조정 내역 로깅
        changes = []
        for trait, adjustment in adjustments.items():
            if trait in base_weights:
                old_val = base_weights[trait]
                new_val = adjusted_weights[trait]
                if abs(old_val - new_val) > 0.01:
                    changes.append(f"{trait}: {old_val:.2f} -> {new_val:.2f}")
        
        if changes:
            print(f"GPT 기반 가중치 조정: {', '.join(changes)}")
        
        return adjusted_weights
    
    def _apply_diversity_filter(self, recommendations, target_count=10):
        """추천 결과에 다양성 필터링 적용"""
        if len(recommendations) <= target_count:
            return recommendations
        
        try:
            engine = self._get_engine()
            selected = [recommendations[0]]  # 첫 번째(가장 높은 점수)는 항상 포함
            
            for candidate in recommendations[1:]:
                if len(selected) >= target_count:
                    break
                
                # 현재 선택된 아이템들과의 평균 유사도 계산
                candidate_id = candidate['item_id']
                if candidate_id not in engine.model['node_embeddings']:
                    selected.append(candidate)
                    continue
                
                candidate_emb = engine.model['node_embeddings'][candidate_id]
                similarities = []
                
                for selected_rec in selected:
                    selected_id = selected_rec['item_id']
                    if selected_id in engine.model['node_embeddings']:
                        selected_emb = engine.model['node_embeddings'][selected_id]
                        from sklearn.metrics.pairwise import cosine_similarity
                        sim = cosine_similarity(
                            candidate_emb.reshape(1, -1),
                            selected_emb.reshape(1, -1)
                        )[0][0]
                        similarities.append(sim)
                
                # 평균 유사도가 임계값 이하인 경우만 선택
                avg_similarity = sum(similarities) / len(similarities) if similarities else 0
                similarity_threshold = 0.6  # 조정 가능한 임계값
                
                if avg_similarity < similarity_threshold:
                    selected.append(candidate)
                    print(f"다양성 필터: 아이템 {candidate_id} 선택 (평균 유사도: {avg_similarity:.3f})")
            
            # 목표 개수에 못 미치는 경우 나머지 채우기
            while len(selected) < target_count and len(selected) < len(recommendations):
                for candidate in recommendations:
                    if candidate not in selected:
                        selected.append(candidate)
                        break
            
            print(f"다양성 필터링 완료: {len(recommendations)} -> {len(selected)}개")
            return selected
            
        except Exception as e:
            print(f"다양성 필터링 오류: {e}")
            return recommendations[:target_count]
    
    def _enhance_weight_differences(self, weights):
        """가중치 차이를 극대화하여 추천 다양성 증대"""
        enhanced = weights.copy()
        
        # 1. 가중치 분포 분석
        values = list(weights.values())
        mean_val = sum(values) / len(values)
        
        # 2. 평균보다 높은 것은 더 높게, 낮은 것은 더 낮게
        for trait, weight in weights.items():
            if weight > mean_val:
                # 높은 가중치는 더 극대화 (최대 0.95)
                enhanced[trait] = min(0.95, weight + (weight - mean_val) * 1.5)
            else:
                # 낮은 가중치는 더 최소화 (최소 0.05)
                enhanced[trait] = max(0.05, weight - (mean_val - weight) * 1.5)
        
        # 3. Big-Five 외의 trait들에 대해서도 더 극단적인 값 부여
        style_traits = ['Elegant', 'Cute', 'Modern', 'Luxurious', 'Warm', 'Vivid', 'Sharp']
        other_traits = ['OSL', 'CNFU', 'MVS', 'CVPA']
        
        # 성격 특성에 따라 스타일 trait 조정
        if enhanced.get('Openness', 0.5) > 0.6:
            enhanced['Modern'] = max(enhanced.get('Modern', 0.5), 0.8)
            enhanced['Vivid'] = max(enhanced.get('Vivid', 0.5), 0.7)
        
        if enhanced.get('Extraversion', 0.5) > 0.6:
            enhanced['Warm'] = max(enhanced.get('Warm', 0.5), 0.8)
            enhanced['Vivid'] = max(enhanced.get('Vivid', 0.5), 0.7)
        
        if enhanced.get('Conscientiousness', 0.5) > 0.6:
            enhanced['Elegant'] = max(enhanced.get('Elegant', 0.5), 0.8)
            enhanced['Luxurious'] = max(enhanced.get('Luxurious', 0.5), 0.7)
        
        if enhanced.get('Agreeableness', 0.5) > 0.6:
            enhanced['Cute'] = max(enhanced.get('Cute', 0.5), 0.8)
            enhanced['Warm'] = max(enhanced.get('Warm', 0.5), 0.7)
        
        return enhanced

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
                "data": None,
                "error": {"code": "INVALID_PRODUCT_ID", "message": "잘못된 상품 ID입니다."}
            }
        
        products_df = self._load_products()
        product = products_df[products_df['product_id'] == product_id_int]
        
        if product.empty:
            return {
                "success": False,
                "data": None,
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

class IntermediateService:
    def __init__(self):
        self.gpt_service = GPTService()
    
    def get_intermediate_result(self, session_id: str) -> Dict[str, Any]:
        """중간 결과 생성 - GPT 기반 성격 분석"""
        try:
            print(f"중간 결과 요청: session_id={session_id}")
            print(f"현재 세션 목록: {list(sessions.keys())}")
            
            if session_id not in sessions:
                print(f"세션 없음: {session_id}")
                return {
                    "success": False,
                    "error": "세션을 찾을 수 없습니다."
                }
            
            session_data = sessions[session_id]
            print(f"세션 데이터: {session_data}")
            user_name = session_data['user_info'].get('name', '사용자')
            
            # 현재까지의 답변이 있는지 확인
            answers = session_data.get('answers', [])
            if len(answers) < 3:  # 최소 3개 답변은 있어야 분석 가능
                print(f"답변 부족: {len(answers)}개")
                return {
                    "success": False,
                    "error": "아직 분석할 데이터가 충분하지 않습니다."
                }
            
            print(f"GPT 호출 시작: user_name={user_name}, answers={len(answers)}개")
            
            # 답변 내용을 GPT가 분석할 수 있도록 정리
            answer_summary = []
            for answer in answers:
                answer_summary.append(f"질문: {answer.get('target_node', '알 수 없음')} 관련, 답변: {answer.get('answer', '없음')}")
            
            # GPT로 중간 결과 생성 (답변 내용 직접 전달)
            gpt_result = self.gpt_service.generate_intermediate_result_from_answers(
                answer_summary, 
                user_name
            )
            
            print(f"GPT 결과: {gpt_result}")
            
            return {
                "success": True,
                "data": {
                    "session_id": session_id,
                    "user_name": user_name,
                    "personality_type": gpt_result["personality_type"],
                    "description": gpt_result["description"],
                    "completion_rate": len(session_data.get('answers', [])) / 44 * 100
                }
            }
            
        except Exception as e:
            print(f"IntermediateService 오류: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "data": None,
                "error": f"중간 결과 생성 중 오류가 발생했습니다: {str(e)}"
            }

# 서비스 인스턴스 생성
user_service = UserService()
test_service = TestService()
recommendation_service = RecommendationService()
product_service = ProductService()
intermediate_service = IntermediateService()