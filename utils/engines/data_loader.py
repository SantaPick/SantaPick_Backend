"""
심리테스트 질문 데이터 로더
"""
import pandas as pd
import os
from pathlib import Path

class PsychologyDataLoader:
    def __init__(self):
        # 백엔드 구조에 맞게 경로 설정
        backend_root = Path(__file__).parent.parent.parent
        self.base_path = backend_root / "data" / "psychology-question"
        
        # 파일 경로들 (trait만 사용)
        self.trait_questions_path = self.base_path / "trait-question.csv"
        self.choice_2_path = self.base_path / "2-choice-question.csv"
        self.choice_4_path = self.base_path / "4-choice-question.csv"
        self.choice_5_path = self.base_path / "5-point-question.csv"
        self.choice_ox_path = self.base_path / "O-X-question.csv"
        
        # 데이터 저장소 (trait만 사용)
        self.trait_questions = None
        self.choice_2_data = None
        self.choice_4_data = None
        self.choice_5_data = None
        self.choice_ox_data = None
        
        # 전체 질문 리스트 (순서대로)
        self.all_questions = []
        
    def load_all_data(self):
        """모든 CSV 파일 로드"""
        print("📂 심리테스트 데이터 로딩 중...")
        
        # 메인 질문 파일 (trait만)
        self.trait_questions = pd.read_csv(self.trait_questions_path)
        
        # 선택지 파일들
        self.choice_2_data = pd.read_csv(self.choice_2_path)
        self.choice_4_data = pd.read_csv(self.choice_4_path)
        self.choice_5_data = pd.read_csv(self.choice_5_path)
        self.choice_ox_data = pd.read_csv(self.choice_ox_path)
        
        print(f"✅ 데이터 로딩 완료!")
        print(f"   - Trait 질문: {len(self.trait_questions)}개")
        
    def create_question_structure(self):
        """질문을 구조화된 형태로 변환"""
        if self.trait_questions is None:
            self.load_all_data()
            
        self.all_questions = []
        
        # 1. Trait 질문들 먼저 추가
        for idx, row in self.trait_questions.iterrows():
            question_data = {
                'id': f"trait_{idx}",
                'category': 'trait',
                'question_type': row['question_type'],
                'question': row['question'],
                'target_node': row['trait_node'],
                'choices': self._get_choices_for_question(row['question_type'], row['question'])
            }
            self.all_questions.append(question_data)
        
        # Concept 질문은 사용하지 않음
            
        print(f"📋 총 {len(self.all_questions)}개 질문 구조화 완료")
        return self.all_questions
    
    def _get_choices_for_question(self, question_type, question_text):
        """질문 타입에 따라 선택지 반환"""
        if question_type == "5_point_question":
            return ["1(매우아님)", "2", "3", "4", "5(매우맞음)"]
        
        elif question_type == "2_choice_question":
            # 2-choice-question.csv에서 해당 질문 찾기
            match_row = self.choice_2_data[self.choice_2_data['question'] == question_text]
            if not match_row.empty:
                row = match_row.iloc[0]
                return [row['response_1'], row['response_2']]
            return ["선택지 1", "선택지 2"]
        
        elif question_type == "4_choice_question":
            # 4-choice-question.csv에서 해당 질문 찾기
            match_row = self.choice_4_data[self.choice_4_data['question'] == question_text]
            if not match_row.empty:
                row = match_row.iloc[0]
                return [row['response_1'], row['response_2'], row['response_3'], row['response_4']]
            return ["선택지 1", "선택지 2", "선택지 3", "선택지 4"]
        
        elif question_type == "O_X_question":
            return ["O", "X"]
        
        return ["기본 선택지"]
    
    def get_question_by_id(self, question_id):
        """ID로 특정 질문 가져오기"""
        for q in self.all_questions:
            if q['id'] == question_id:
                return q
        return None
    
    def get_questions_by_category(self, category):
        """카테고리별 질문 가져오기"""
        return [q for q in self.all_questions if q['category'] == category]

# 테스트 코드
if __name__ == "__main__":
    loader = PsychologyDataLoader()
    questions = loader.create_question_structure()
    
    print("\n📋 질문 구조 테스트:")
    for i, q in enumerate(questions[:3]):  # 처음 3개만 출력
        print(f"{i+1}. [{q['category']}] {q['question_type']}")
        print(f"   질문: {q['question']}")
        print(f"   노드: {q['target_node']}")
        print(f"   선택지: {q['choices']}")
        print()