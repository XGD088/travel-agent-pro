import os
import chromadb
from chromadb.config import Settings
from typing import List, Dict, Any, Optional
from ..logging_config import get_logger

logger = get_logger(__name__)

class VectorDBService:
    """向量数据库服务类 - 管理ChromaDB连接和操作"""
    
    def __init__(self):
        """初始化ChromaDB客户端"""
        self.client = None
        self.collection = None
        self.collection_name = "beijing_poi"
        logger.info("🔧 初始化向量数据库服务")
    
    def _get_client(self):
        """延迟初始化ChromaDB客户端"""
        if self.client is None:
            chroma_host = os.getenv("CHROMA_HOST", "localhost")
            chroma_port = int(os.getenv("CHROMA_PORT", "8001"))
            
            logger.info(f"🔗 连接到ChromaDB: {chroma_host}:{chroma_port}")
            
            try:
                # 尝试连接到远程ChromaDB服务
                self.client = chromadb.HttpClient(
                    host=chroma_host,
                    port=chroma_port,
                    settings=Settings(allow_reset=True)
                )
                # 测试连接
                self.client.heartbeat()
                logger.info("✅ ChromaDB连接成功")
            except Exception as e:
                logger.warning(f"⚠️ 无法连接到远程ChromaDB，回退到本地模式: {e}")
                # 回退到本地ChromaDB
                self.client = chromadb.Client()
                
        return self.client
    
    def get_or_create_collection(self):
        """获取或创建POI向量集合"""
        if self.collection is None:
            client = self._get_client()
            try:
                # 尝试获取现有集合
                self.collection = client.get_collection(name=self.collection_name)
                logger.info(f"📚 获取现有集合: {self.collection_name}")
            except Exception:
                # 创建新集合
                self.collection = client.create_collection(
                    name=self.collection_name,
                    metadata={"description": "北京POI向量存储"}
                )
                logger.info(f"📚 创建新集合: {self.collection_name}")
                
        return self.collection
    
    def add_documents(self, documents: List[str], metadatas: List[Dict], ids: List[str]):
        """添加文档到向量数据库"""
        collection = self.get_or_create_collection()
        
        try:
            collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            logger.info(f"✅ 成功添加 {len(documents)} 个POI文档到向量数据库")
        except Exception as e:
            logger.error(f"❌ 添加文档失败: {e}")
            raise
    
    def search_similar(self, query_text: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """搜索相似POI"""
        collection = self.get_or_create_collection()
        
        try:
            results = collection.query(
                query_texts=[query_text],
                n_results=n_results,
                include=['documents', 'metadatas', 'distances']
            )
            
            # 格式化返回结果
            formatted_results = []
            if results['documents'] and results['documents'][0]:
                for i in range(len(results['documents'][0])):
                    formatted_results.append({
                        'document': results['documents'][0][i],
                        'metadata': results['metadatas'][0][i] if results['metadatas'][0] else {},
                        'distance': results['distances'][0][i] if results['distances'][0] else 0
                    })
            
            logger.info(f"🔍 找到 {len(formatted_results)} 个相似POI")
            return formatted_results
            
        except Exception as e:
            logger.error(f"❌ 搜索失败: {e}")
            return []
    
    def get_collection_count(self) -> int:
        """获取集合中的文档数量"""
        try:
            collection = self.get_or_create_collection()
            count = collection.count()
            logger.info(f"📊 集合中共有 {count} 个POI")
            return count
        except Exception as e:
            logger.error(f"❌ 获取集合数量失败: {e}")
            return 0 