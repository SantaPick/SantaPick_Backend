import os
import openai
from typing import Dict, Any
from dotenv import load_dotenv

# 환경변수 로드
load_dotenv()

class GPTService:
    def __init__(self):
        self.client = openai.OpenAI(
            api_key=os.getenv("OPENAI_API_KEY")
        )
    
    def generate_intermediate_result(self, user_traits: Dict[str, float], user_name: str) -> Dict[str, str]:
        """
        중간 결과 생성: 사용자의 성격 특성을 바탕으로 한 단어와 설명 생성
        """
        # 가장 높은 점수의 특성들 추출
        top_traits = sorted(user_traits.items(), key=lambda x: x[1], reverse=True)[:3]
        trait_descriptions = []
        
        for trait, score in top_traits:
            trait_descriptions.append(f"{trait}: {score:.2f}")
        
        prompt = f"""
사용자 {user_name}님의 심리테스트 중간 결과를 분석해주세요.

현재까지의 성격 특성 점수:
{chr(10).join(trait_descriptions)}

다음 형식으로 응답해주세요:
1. 한 단어 또는 짧은 구문 (예: "감성적인 로맨티스트", "논리적인 현실주의자")
2. 해당 성격에 대한 짧은 설명 (1-2문장, 50자 이내)

응답 형식:
성격유형: [한 단어/구문]
설명: [짧은 설명]
"""

        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "당신은 심리학 전문가입니다. 성격 분석을 정확하고 간결하게 제공합니다."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=150,
                temperature=0.7
            )
            
            result_text = response.choices[0].message.content.strip()
            
            # 응답 파싱
            lines = result_text.split('\n')
            personality_type = ""
            description = ""
            
            for line in lines:
                if line.startswith("성격유형:"):
                    personality_type = line.replace("성격유형:", "").strip()
                elif line.startswith("설명:"):
                    description = line.replace("설명:", "").strip()
            
            return {
                "personality_type": personality_type or "분석 중인 성격",
                "description": description or "현재까지의 결과를 분석하고 있습니다."
            }
            
        except Exception as e:
            print(f"GPT API 오류: {e}")
            # 기본값 반환
            return {
                "personality_type": "분석 중인 성격",
                "description": "현재까지의 결과를 종합하여 분석하고 있습니다."
            }
    
    def generate_intermediate_result_from_answers(self, answer_summary: list, user_name: str) -> Dict[str, str]:
        """
        답변 내용을 직접 분석하여 중간 결과 생성
        """
        answers_text = "\n".join(answer_summary)
        
        prompt = f"""
사용자 {user_name}님의 심리테스트 중간 답변을 분석해주세요.

현재까지의 답변 내용:
{answers_text}

이 답변들을 바탕으로 다음 형식으로 응답해주세요:
1. 한 단어 또는 짧은 구문 (예: "감성적인 로맨티스트", "논리적인 현실주의자")
2. 해당 성격에 대한 짧은 설명 (1-2문장, 50자 이내)

응답 형식:
성격유형: [한 단어/구문]
설명: [짧은 설명]
"""

        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "당신은 심리학 전문가입니다. 답변 내용을 바탕으로 성격을 분석합니다."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=150,
                temperature=0.7
            )
            
            result_text = response.choices[0].message.content.strip()
            
            # 응답 파싱
            lines = result_text.split('\n')
            personality_type = ""
            description = ""
            
            for line in lines:
                if line.startswith("성격유형:"):
                    personality_type = line.replace("성격유형:", "").strip()
                elif line.startswith("설명:"):
                    description = line.replace("설명:", "").strip()
            
            return {
                "personality_type": personality_type or "분석 중인 성격",
                "description": description or "현재까지의 답변을 바탕으로 분석한 결과입니다."
            }
            
        except Exception as e:
            print(f"GPT API 오류: {e}")
            return {
                "personality_type": "분석 중인 성격",
                "description": "현재까지의 답변을 바탕으로 분석하고 있습니다."
            }
    
    def generate_final_result(self, user_traits: Dict[str, float], user_name: str, all_answers: list) -> Dict[str, str]:
        """
        최종 결과 생성: 모든 답변과 성격 특성을 바탕으로 더 구체적인 분석 제공
        """
        # 성격 특성 점수를 텍스트로 변환
        trait_descriptions = []
        for trait, score in user_traits.items():
            trait_descriptions.append(f"{trait}: {score:.2f}")
        
        # 답변 요약
        answers_summary = []
        for i, answer in enumerate(all_answers[:10]):  # 처음 10개 답변만 요약
            answers_summary.append(f"Q{i+1}: {answer.get('answer', 'N/A')}")
        
        prompt = f"""
{user_name}님의 심리테스트가 완료되었습니다. 최종 분석을 제공해주세요.

성격 특성 점수:
{chr(10).join(trait_descriptions)}

주요 답변 내용:
{chr(10).join(answers_summary)}

다음 형식으로 응답해주세요:
1. 성격 유형: 매력적인 명사형 표현 (예: "창의적 감성주의자", "따뜻한 리더", "자유로운 모험가", "세심한 완벽주의자")
2. 상세 설명: 해당 성격에 대한 구체적이고 긍정적인 설명 (2-3문장, 100자 내외)

중요: 성격 유형은 반드시 명사로 끝나야 합니다. "~한 사람", "~이고 ~인 리더" 같은 명사형 표현을 사용하세요.

응답 형식:
성격유형: [성격 유형]
설명: [상세 설명]
"""

        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "당신은 전문 심리학자입니다. 사용자의 성격을 긍정적이고 구체적으로 분석하여 매력적인 결과를 제공합니다."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=200,
                temperature=0.8
            )
            
            result_text = response.choices[0].message.content.strip()
            
            # 응답 파싱
            lines = result_text.split('\n')
            personality_type = ""
            description = ""
            
            for line in lines:
                if line.startswith("성격유형:"):
                    personality_type = line.replace("성격유형:", "").strip()
                elif line.startswith("설명:"):
                    description = line.replace("설명:", "").strip()
            
            return {
                "personality_type": personality_type or "매력적인 개성",
                "description": description or f"{user_name}님은 독특하고 매력적인 성격을 가지고 계십니다. 당신만의 특별한 개성이 돋보입니다."
            }
            
        except Exception as e:
            print(f"GPT API 오류: {e}")
            return {
                "personality_type": "매력적인 개성",
                "description": f"{user_name}님은 독특하고 매력적인 성격을 가지고 계십니다. 당신만의 특별한 개성이 돋보입니다."
            }