import os
import requests
from typing import List, Optional
import numpy as np
from ..logging_config import get_logger

logger = get_logger(__name__)

class EmbeddingService:
    """文本嵌入服务类 - 使用Qwen Embedding API"""
    
    def __init__(self):
        """初始化Qwen Embedding服务"""
        self.api_key = os.getenv("DASHSCOPE_API_KEY")
        self.base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1/embeddings"
        self.model = None
        logger.info("🔧 初始化Qwen Embedding服务")
        
        # 检查API key是否成功加载
        if not self.api_key:
            logger.error("❌ DASHSCOPE_API_KEY 环境变量未设置")
            logger.info("💡 请检查.env文件或设置环境变量: export DASHSCOPE_API_KEY='your-api-key'")
        else:
            logger.info("✅ DASHSCOPE_API_KEY 已成功加载")
    
    def _get_headers(self):
        """获取API请求头"""
        if not self.api_key:
            raise ValueError("DASHSCOPE_API_KEY 环境变量未设置")
        
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def _call_qwen_embedding(self, text: str) -> List[float]:
        """调用Qwen Embedding API"""
        try:
            headers = self._get_headers()
            payload = {
                "model": "text-embedding-v4",
                "input": text
            }
            
            logger.debug(f"📡 调用Qwen Embedding API: {text[:50]}...")
            response = requests.post(self.base_url, headers=headers, json=payload, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                embedding = result['data'][0]['embedding']
                logger.debug(f"✅ 成功获取嵌入向量，维度: {len(embedding)}")
                return embedding
            else:
                logger.error(f"❌ Qwen Embedding API调用失败: {response.status_code} - {response.text}")
                raise Exception(f"API调用失败: {response.status_code}")
                
        except Exception as e:
            logger.error(f"❌ Qwen Embedding调用异常: {e}")
            raise
    
    def encode_text(self, text: str) -> List[float]:
        """将单个文本编码为向量"""
        try:
            embedding = self._call_qwen_embedding(text)
            return embedding
        except Exception as e:
            logger.error(f"❌ 文本编码失败: {e}")
            return []
    
    def encode_texts(self, texts: List[str]) -> List[List[float]]:
        """批量编码文本列表"""
        try:
            embeddings = []
            for i, text in enumerate(texts):
                logger.debug(f"🔢 编码文本 {i+1}/{len(texts)}: {text[:30]}...")
                embedding = self._call_qwen_embedding(text)
                embeddings.append(embedding)
            
            logger.info(f"✅ 批量编码完成，共 {len(embeddings)} 个文本")
            return embeddings
            
        except Exception as e:
            logger.error(f"❌ 批量文本编码失败: {e}")
            return []
    
    def get_embedding_dimension(self) -> int:
        """获取嵌入向量的维度"""
        try:
            # 使用测试文本获取维度
            test_embedding = self._call_qwen_embedding("测试文本")
            dimension = len(test_embedding)
            logger.info(f"📊 Qwen Embedding维度: {dimension}")
            return dimension
        except Exception as e:
            logger.error(f"❌ 获取嵌入维度失败: {e}")
            return 1536  # Qwen Embedding默认维度
    
    def similarity(self, text1: str, text2: str) -> float:
        """计算两个文本的相似度"""
        try:
            embedding1 = np.array(self._call_qwen_embedding(text1))
            embedding2 = np.array(self._call_qwen_embedding(text2))
            
            # 计算余弦相似度
            similarity = np.dot(embedding1, embedding2) / (np.linalg.norm(embedding1) * np.linalg.norm(embedding2))
            return float(similarity)
        except Exception as e:
            logger.error(f"❌ 相似度计算失败: {e}")
            return 0.0
    
    def test_connection(self) -> bool:
        """测试Qwen Embedding API连接"""
        try:
            test_embedding = self._call_qwen_embedding("测试连接")
            logger.info("✅ Qwen Embedding API连接正常")
            return True
        except Exception as e:
            logger.error(f"❌ Qwen Embedding API连接失败: {e}")
            return False 