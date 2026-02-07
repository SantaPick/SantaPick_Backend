"""
추천 엔진 - 그래프에 User 노드 추가 및 추천 생성
"""
import pickle
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.metrics.pairwise import cosine_similarity

class RecommendationEngine:
    def __init__(self):
        self.model = None
        # 백엔드 구조에 맞게 경로 수정
        base_path = Path(__file__).parent.parent
        self.embeddings_path = base_path / "models" / "embeddings.pkl"
        self.graph_path = base_path / "models" / "recommendation_graph.pkl"
        self.user_id_counter = 2000
        
    def load_model(self):
        """학습된 모델과 그래프 로드"""
        print("모델 로딩 중...")
        
        try:
            # 임베딩 로드
            with open(self.embeddings_path, 'rb') as f:
                embedding_data = pickle.load(f)
            
            # 그래프 로드
            with open(self.graph_path, 'rb') as f:
                graph_data = pickle.load(f)
            
            self.model = {
                'graph': graph_data['graph'],
                'node_types': graph_data.get('node_types', {}),
                'node_id_mapping': graph_data.get('node_id_mapping', {}),
                'node_embeddings': embedding_data.get('embeddings', {}),
                'embedding_dim': len(list(embedding_data.get('embeddings', {}).values())[0]) if embedding_data.get('embeddings') else 128
            }
            
            print(f"모델 로드 완료: {len(self.model['node_embeddings'])}개 노드 임베딩")
            
        except Exception as e:
            print(f"모델 로드 실패: {e}")
            raise e
        
    def add_user_node(self, user_weights):
        """User 노드를 그래프에 추가하고 임베딩 생성"""
        if self.model is None:
            self.load_model()
        
        user_id = self.user_id_counter
        self.user_id_counter += 1
        
        # 그래프에 User 노드 추가 (임시로 추가하지 않고 임베딩만 생성)
        user_edges = []
        for node_name, weight in user_weights.items():
            # 노드 이름을 ID로 변환
            node_id = self._get_node_id_by_name(node_name)
            if node_id and node_id in self.model['node_embeddings']:
                user_edges.append((node_id, weight))
        
        # User 임베딩 생성 (연결된 노드들의 가중평균)
        user_embedding = self._generate_user_embedding(user_edges)
        self.model['node_embeddings'][user_id] = user_embedding
        
        print(f"User 노드 추가 완료: {user_id}, 연결된 노드: {len(user_edges)}개")
        return user_id
    
    def _get_node_id_by_name(self, node_name):
        """노드 이름으로 ID 찾기"""
        for name, data in self.model['node_id_mapping'].items():
            if name == node_name:
                return data['id']
        return None
    
    def _is_trait_node(self, node_name):
        """Trait 노드인지 확인"""
        trait_nodes = ['Openness', 'Conscientiousness', 'Extraversion', 'Agreeableness', 'Neuroticism',
                      'Elegant', 'Cute', 'Modern', 'Luxurious', 'Warm', 'Vivid', 'Sharp',
                      'OSL', 'CNFU', 'MVS', 'CVPA']
        return node_name in trait_nodes
    
    def _generate_user_embedding(self, user_edges):
        """User 임베딩 생성 (연결된 노드들의 가중평균)"""
        if not user_edges:
            return np.random.normal(0, 0.1, self.model['embedding_dim'])
        
        user_embedding = np.zeros(self.model['embedding_dim'])
        total_weight = 0
        
        for node_id, weight in user_edges:
            if node_id in self.model['node_embeddings']:
                user_embedding += self.model['node_embeddings'][node_id] * abs(weight)
                total_weight += abs(weight)
        
        if total_weight > 0:
            user_embedding /= total_weight
        else:
            user_embedding = np.random.normal(0, 0.1, self.model['embedding_dim'])
        
        return user_embedding
    
    def get_recommendations(self, user_id, top_k=10):
        """User에게 아이템 추천"""
        if user_id not in self.model['node_embeddings']:
            raise ValueError(f"User {user_id}의 임베딩이 없습니다.")
        
        user_embedding = self.model['node_embeddings'][user_id]
        
        # 아이템 노드들과 유사도 계산
        item_similarities = []
        for item_id in self.model['node_types'].get('item', []):
            if item_id in self.model['node_embeddings']:
                item_embedding = self.model['node_embeddings'][item_id]
                similarity = cosine_similarity(
                    user_embedding.reshape(1, -1),
                    item_embedding.reshape(1, -1)
                )[0][0]
                
                item_data = self.model['graph'].nodes[item_id]
                item_similarities.append({
                    'item_id': item_id,
                    'item_name': item_data.get('name', f'item_{item_id}'),
                    'similarity': similarity
                })
        
        # 유사도 기준 정렬
        item_similarities.sort(key=lambda x: x['similarity'], reverse=True)
        return item_similarities[:top_k]
    
    def get_item_details(self, recommendations):
        """추천 아이템의 상세 정보 추가"""
        try:
            # products.csv에서 상품 정보 로드
            products_csv_path = Path("data/product/products.csv")
            if products_csv_path.exists():
                products_df = pd.read_csv(products_csv_path)
                
                for rec in recommendations:
                    node_id = rec['item_id']  # 이것은 노드 ID (1000번대)
                    
                    # 노드 ID → 상품 ID 매핑
                    product_id = self._get_product_id_by_node_id(node_id)
                    
                    if product_id:
                        # 상품 ID → 상품 정보 매핑
                        product_row = products_df[products_df['product_id'].astype(str) == str(product_id)]
                        if not product_row.empty:
                            row = product_row.iloc[0]
                            rec['product_id'] = product_id
                            rec['name'] = row.get('name', rec['item_name'])
                            rec['price'] = f"{row.get('price', 0):,}원" if pd.notna(row.get('price')) else 'N/A'
                            rec['category'] = row.get('category', 'N/A')
                            rec['description'] = row.get('description', 'N/A')[:200] + '...' if pd.notna(row.get('description')) and len(str(row.get('description'))) > 200 else row.get('description', 'N/A')
                            rec['image_path'] = f"data/product/{row.get('image_path', '')}" if pd.notna(row.get('image_path')) else None
                        else:
                            rec['product_id'] = product_id
                            rec['name'] = f'상품 {product_id}'
                            rec['price'] = 'N/A'
                            rec['category'] = 'N/A'
                            rec['description'] = 'N/A'
                            rec['image_path'] = None
                    else:
                        rec['product_id'] = None
                        rec['name'] = f'노드 {node_id}'
                        rec['price'] = 'N/A'
                        rec['category'] = 'N/A'
                        rec['description'] = 'N/A'
                        rec['image_path'] = None
        except Exception as e:
            print(f"상품 정보 로드 실패: {e}")
        
        return recommendations
    
    def _get_product_id_by_node_id(self, node_id):
        """노드 ID로 실제 상품 ID 찾기"""
        for product_id, data in self.model['node_id_mapping'].items():
            if data.get('id') == node_id:
                return product_id
        return None

# 테스트 코드
if __name__ == "__main__":
    engine = RecommendationEngine()
    
    # 테스트 가중치
    test_weights = {
        'Extraversion': 0.8,
        'Openness': 0.6,
        'Unique': 0.4
    }
    
    try:
        user_id = engine.add_user_node(test_weights)
        recommendations = engine.get_recommendations(user_id, top_k=5)
        recommendations = engine.get_item_details(recommendations)
        
        print(f"\nUser {user_id} 추천 결과:")
        for i, rec in enumerate(recommendations, 1):
            print(f"{i}. {rec['item_name']} (유사도: {rec['similarity']:.3f})")
            
    except Exception as e:
        print(f"테스트 실패: {e}")