import json
import os
from typing import List, Dict, Any
from .vector_service import VectorDBService
from .embedding_service import EmbeddingService
from ..config import get_settings
from ..logging_config import get_logger

logger = get_logger(__name__)

class POIEmbeddingService:
    """POI嵌入服务类 - 负责POI数据的向量化和存储"""
    
    def __init__(self):
        """初始化POI嵌入服务"""
        settings = get_settings()
        self.vector_service = VectorDBService()
        self.embedding_service = EmbeddingService(api_key=settings.DASHSCOPE_API_KEY)
        self.poi_data_path = os.path.join(os.path.dirname(__file__), "..", "data", "beijing_poi.json")
        logger.info("🔧 初始化POI嵌入服务")
    
    def load_poi_data(self) -> List[Dict[str, Any]]:
        """加载POI数据"""
        try:
            with open(self.poi_data_path, 'r', encoding='utf-8') as f:
                poi_data = json.load(f)
            logger.info(f"📚 成功加载 {len(poi_data)} 条POI数据")
            return poi_data
        except Exception as e:
            logger.error(f"❌ 加载POI数据失败: {e}")
            return []
    
    def create_poi_document(self, poi: Dict[str, Any]) -> str:
        """为POI创建文档描述"""
        # 构建包含POI所有重要信息的文档
        document = f"""
        {poi['name']} - {poi['type']}
        地址: {poi['address']}
        评分: {poi['rating']}
        门票: {poi['ticket_price']}元
        营业时间: {poi['business_hours']}
        标签: {', '.join(poi['tags'])}
        
        详细介绍:
        {poi['description']}
        """
        return document.strip()
    
    def create_poi_metadata(self, poi: Dict[str, Any]) -> Dict[str, Any]:
        """为POI创建元数据"""
        return {
            "id": poi['id'],
            "name": poi['name'],
            "type": poi['type'],
            "address": poi['address'],
            "rating": poi['rating'],
            "ticket_price": poi['ticket_price'],
            "business_hours": poi['business_hours'],
            "tags": ', '.join(poi['tags'])  # 将列表转换为字符串
        }
    
    def embed_and_store_pois(self) -> bool:
        """将POI数据向量化并存储到向量数据库"""
        try:
            # 检查Qwen Embedding API可用性
            if not self._check_embedding_service():
                logger.error("❌ Qwen Embedding服务不可用")
                return False
            
            # 加载POI数据
            poi_data = self.load_poi_data()
            if not poi_data:
                logger.error("❌ 没有可用的POI数据")
                return False
            
            # 准备文档和元数据
            documents = []
            metadatas = []
            ids = []
            
            for poi in poi_data:
                document = self.create_poi_document(poi)
                metadata = self.create_poi_metadata(poi)
                
                documents.append(document)
                metadatas.append(metadata)
                ids.append(poi['id'])
            
            # 存储到向量数据库
            self.vector_service.add_documents(documents, metadatas, ids)
            
            logger.info(f"✅ 成功向量化并存储 {len(poi_data)} 个POI")
            return True
            
        except Exception as e:
            logger.error(f"❌ POI向量化存储失败: {e}")
            return False
    
    def _check_embedding_service(self) -> bool:
        """检查嵌入服务可用性"""
        try:
            # 测试Qwen Embedding连接
            if hasattr(self.embedding_service, 'test_connection'):
                return self.embedding_service.test_connection()
            else:
                # 如果没有test_connection方法，尝试简单编码
                test_embedding = self.embedding_service.encode_text("测试")
                return len(test_embedding) > 0
        except Exception as e:
            logger.warning(f"⚠️ 嵌入服务检查失败: {e}")
            return False
    
    def search_pois_by_query(self, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """根据查询搜索相关POI"""
        try:
            # 检查嵌入服务可用性
            if not self._check_embedding_service():
                logger.error("❌ 嵌入服务不可用，无法进行搜索")
                return []
            
            results = self.vector_service.search_similar(query, n_results)
            
            # 格式化搜索结果
            formatted_results = []
            for result in results:
                formatted_results.append({
                    'poi_info': result['metadata'],
                    'description': result['document'],
                    'similarity_score': 1 - result['distance']  # 转换为相似度分数
                })
            
            logger.info(f"🔍 查询 '{query}' 找到 {len(formatted_results)} 个相关POI")
            return formatted_results
            
        except Exception as e:
            logger.error(f"❌ POI搜索失败: {e}")
            return []
    
    def get_poi_recommendations(self, theme: str, duration_days: int) -> List[Dict[str, Any]]:
        """根据主题和天数推荐POI"""
        try:
            # 检查嵌入服务可用性
            if not self._check_embedding_service():
                logger.error("❌ 嵌入服务不可用，无法进行推荐")
                return []
            
            # 构建推荐查询
            query = f"北京{theme}旅游景点推荐，适合{duration_days}天行程"
            
            # 根据天数调整推荐数量
            n_recommendations = min(duration_days * 3, 15)  # 每天3个景点，最多15个
            
            recommendations = self.search_pois_by_query(query, n_recommendations)
            
            logger.info(f"🎯 为'{theme}'主题{duration_days}天行程推荐了 {len(recommendations)} 个POI")
            return recommendations
            
        except Exception as e:
            logger.error(f"❌ POI推荐失败: {e}")
            return []
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """获取向量数据库统计信息"""
        try:
            count = self.vector_service.get_collection_count()
            embedding_dimension = self.embedding_service.get_embedding_dimension()
            
            stats = {
                "total_pois": count,
                "embedding_dimension": embedding_dimension,
                "status": "ready" if count > 0 else "empty",
                "embedding_service": "Qwen Embedding API"
            }
            
            # 检查嵌入服务状态
            if self._check_embedding_service():
                stats["embedding_status"] = "available"
            else:
                stats["embedding_status"] = "unavailable"
            
            return stats
            
        except Exception as e:
            logger.error(f"❌ 获取统计信息失败: {e}")
            return {"status": "error", "error": str(e)} 