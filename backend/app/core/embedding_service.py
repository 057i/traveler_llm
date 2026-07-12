"""
Embedding Service - 本地Embedding模型服务

使用本地bge-base-zh-v1.5模型生成稠密向量
使用TF-IDF生成稀疏向量（BM25风格）
"""
from sentence_transformers import SentenceTransformer
from sklearn.feature_extraction.text import TfidfVectorizer
from typing import List, Union, Dict
from loguru import logger
from config.settings import settings
import jieba


class EmbeddingService:
    """本地Embedding模型服务 - 支持稠密向量和稀疏向量"""

    def __init__(self):
        self.model_path = settings.EMBEDDING_MODEL
        self.dimension = settings.EMBEDDING_DIM
        self.dense_model = None
        self.sparse_vectorizer = None

    def load_model(self):
        """加载本地embedding模型"""
        if self.dense_model is None:
            logger.info(f"[Embedding] Loading dense model: {self.model_path}")
            try:
                self.dense_model = SentenceTransformer(self.model_path)
                logger.success(f"[Embedding] Dense model loaded (dim={self.dimension})")
            except Exception as e:
                logger.error(f"[Embedding] Failed to load dense model: {e}")
                raise

    def encode(self, texts: Union[str, List[str]], normalize_embeddings: bool = False) -> Union[List[float], List[List[float]]]:
        """
        生成稠密向量

        Args:
            texts: 单个文本或文本列表
            normalize_embeddings: 是否归一化向量（提升性能）

        Returns:
            向量或向量列表
        """
        if self.dense_model is None:
            self.load_model()

        # 处理单个文本
        if isinstance(texts, str):
            texts = [texts]
            single = True
        else:
            single = False

        # 生成向量（添加normalize参数）
        embeddings = self.dense_model.encode(
            texts,
            convert_to_numpy=True,
            normalize_embeddings=normalize_embeddings,
            show_progress_bar=False
        )

        # 转换为列表
        result = embeddings.tolist()

        # 如果输入是单个文本，返回单个向量
        if single:
            return result[0]

        return result

    def encode_sparse(self, texts: List[str]) -> List[Dict[int, float]]:
        """
        生成稀疏向量（BM25风格）

        Args:
            texts: 文本列表

        Returns:
            稀疏向量列表，格式为 [{idx: value}, ...]
        """
        # 中文分词函数
        def tokenize_chinese(text):
            return list(jieba.cut(text))

        # 初始化TF-IDF向量器
        if self.sparse_vectorizer is None:
            logger.info("[Embedding] Initializing sparse vectorizer")
            self.sparse_vectorizer = TfidfVectorizer(
                tokenizer=tokenize_chinese,
                max_features=10000,
                min_df=1,
                token_pattern=None
            )
            # 拟合数据
            self.sparse_vectorizer.fit(texts)

        # 生成TF-IDF向量
        sparse_matrix = self.sparse_vectorizer.transform(texts)

        # 转换为稀疏字典格式
        sparse_vectors = []
        for i in range(sparse_matrix.shape[0]):
            row = sparse_matrix.getrow(i)
            sparse_dict = {
                int(idx): float(val)
                for idx, val in zip(row.indices, row.data)
                if val > 0  # 只保留非零值
            }
            sparse_vectors.append(sparse_dict)

        logger.info(f"[Embedding] Generated {len(sparse_vectors)} sparse vectors")
        return sparse_vectors


# 单例
_embedding_service = None


def get_embedding_service() -> EmbeddingService:
    """获取Embedding服务单例"""
    global _embedding_service

    if _embedding_service is None:
        _embedding_service = EmbeddingService()

    return _embedding_service
