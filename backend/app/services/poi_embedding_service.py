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
        # 添加内存缓存，避免重复加载
        self._poi_data_cache: List[Dict[str, Any]] = []
        self._cache_loaded = False
        logger.info("🔧 初始化POI嵌入服务")
    
    def load_poi_data(self) -> List[Dict[str, Any]]:
        """加载POI数据（带缓存机制）"""
        # 如果已经缓存，直接返回
        if self._cache_loaded and self._poi_data_cache:
            logger.debug(f"📚 使用缓存的POI数据: {len(self._poi_data_cache)} 条")
            return self._poi_data_cache
            
        # 首次加载
        try:
            with open(self.poi_data_path, 'r', encoding='utf-8') as f:
                poi_data = json.load(f)
            
            # 缓存数据
            self._poi_data_cache = poi_data
            self._cache_loaded = True
            
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
 