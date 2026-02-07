"""
심리테스트 응답을 가중치로 변환하는 계산기
"""
import pandas as pd
from pathlib import Path

class ScoringCalculator:
    def __init__(self):
        # 백엔드 구조에 맞게 경로 설정
        backend_root = Path(__file__).parent.parent.parent
        self.base_path = backend_root / "data" / "psychology-question"
        
        # 참조 파일들 로드
        self.choice_2_data = pd.read_csv(self.base_path / "2-choice-question.csv")
        self.choice_4_data = pd.read_csv(self.base_path / "4-choice-question.csv")
        self.choice_5_data = pd.read_csv(self.base_path / "5-point-question.csv")
        self.choice_ox_data = pd.read_csv(self.base_path / "O-X-question.csv")
        
    def calculate_user_weights(self, answers):
        """사용자 답변을 기반으로 노드별 가중치 계산"""
        user_weights = {}
        
        for answer_id, answer_data in answers.items():
            # 프론트엔드 데이터 형식에 맞게 수정
            target_node = answer_data.get('target_node', 'Openness')
            answer_text = answer_data.get('answer', '')
            
            # 답변 형식에 따라 질문 타입 추정
            if answer_text in ['O', 'X']:
                question_type = "O_X_question"
                choice_index = 0 if answer_text == 'O' else 1
            elif answer_text.startswith('1(') or answer_text in ['1', '2', '3', '4', '5']:
                question_type = "5_point_question"
                if answer_text.startswith('1('):
                    choice_index = 0
                else:
                    choice_index = int(answer_text) - 1
            elif len(answer_text) > 10:  # 긴 텍스트는 2선택 또는 4선택
                question_type = "2_choice_question"
                choice_index = 0  # 임시값
            else:
                question_type = "2_choice_question"
                choice_index = 0
            
            selected_choice = answer_text
            question = f"Question for {target_node}"
            
            # 질문 타입별 가중치 계산
            if question_type == "5_point_question":
                weight = self._calculate_5point_weight(question, selected_choice, choice_index, target_node)
            elif question_type == "2_choice_question":
                weight = self._calculate_2choice_weight(question, choice_index)
            elif question_type == "4_choice_question":
                weight = self._calculate_4choice_weight(question, choice_index)
            elif question_type == "O_X_question":
                weight = self._calculate_ox_weight(question, choice_index)
            else:
                continue
                
            # 가중치 저장
            if target_node not in user_weights:
                user_weights[target_node] = []
            user_weights[target_node].append(weight)
        
        # 동일 노드의 다중 질문은 평균값 사용
        final_weights = {}
        for node, weights in user_weights.items():
            final_weights[node] = sum(weights) / len(weights)
        
        # Pref_ 노드 처리
        self._process_pref_nodes(final_weights)
        
        # 가중치 범위 클리핑 (-1 ~ 1)
        for node in final_weights:
            final_weights[node] = max(-1.0, min(1.0, final_weights[node]))
            
        return final_weights
    
    def _calculate_5point_weight(self, question, selected_choice, choice_index, target_node):
        """5-point 질문 가중치 계산"""
        # 1->0.2, 2->0.4, 3->0.6, 4->0.8, 5->1.0
        base_weight = (choice_index + 1) * 0.2
        
        # positive_negative_relation 확인
        relation_row = self.choice_5_data[self.choice_5_data['question'] == question]
        if not relation_row.empty:
            relation = relation_row.iloc[0]['positive_negative_relation']
            if relation == '-':
                base_weight = -base_weight
        
        return base_weight
    
    def _calculate_2choice_weight(self, question, choice_index):
        """2-choice 질문 가중치 계산"""
        relation_row = self.choice_2_data[self.choice_2_data['question'] == question]
        if not relation_row.empty:
            row = relation_row.iloc[0]
            if choice_index == 0:  # response_1
                return 0.7 if row['pn_response_1'] == '+' else -0.7
            else:  # response_2
                return 0.7 if row['pn_response_2'] == '+' else -0.7
        return 0.0
    
    def _calculate_4choice_weight(self, question, choice_index):
        """4-choice 질문 가중치 계산"""
        relation_row = self.choice_4_data[self.choice_4_data['question'] == question]
        if not relation_row.empty:
            row = relation_row.iloc[0]
            pn_col = f'pn_response_{choice_index + 1}'
            if pn_col in row:
                return 0.7 if row[pn_col] == '+' else -0.7
        return 0.0
    
    def _calculate_ox_weight(self, question, choice_index):
        """O-X 질문 가중치 계산"""
        relation_row = self.choice_ox_data[self.choice_ox_data['question'] == question]
        if not relation_row.empty:
            row = relation_row.iloc[0]
            if choice_index == 0:  # O
                return 0.7 if row['pn_response_1'] == '+' else -0.7
            else:  # X
                return 0.7 if row['pn_response_2'] == '+' else -0.7
        return 0.0
    
    def _process_pref_nodes(self, weights):
        """Pref_ 노드 처리 (concept 관련 로직 제거)"""
        pref_nodes = [node for node in weights.keys() if node.startswith('Pref_')]
        
        for pref_node in pref_nodes:
            # Pref_Elegant -> Elegant로 단순 변경만
            emotion_name = pref_node.replace('Pref_', '')
            weights[emotion_name] = weights.pop(pref_node)

# 테스트 코드
if __name__ == "__main__":
    calculator = ScoringCalculator()
    
    # 테스트 답변 데이터
    test_answers = {
        'trait_0': {
            'question': '남들의 주목을 받는 것이 딱히 부담스럽지 않고 개의치 않는다.',
            'question_type': '5_point_question',
            'target_node': 'Extraversion',
            'selected_choice': '4',
            'choice_index': 3
        }
    }
    
    weights = calculator.calculate_user_weights(test_answers)
    print("계산된 가중치:", weights)