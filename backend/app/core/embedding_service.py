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
    """
    本地Embedding模型服务

    功能：
    - 支持稠密向量生成（Dense Vector）- 使用 bge-base-zh-v1.5 模型
    - 支持稀疏向量生成（Sparse Vector）- 使用 TF-IDF + jieba 分词
    - 提供向量归一化选项

    应用场景：
    - 语义相似度搜索（稠密向量）
    - 关键词精确匹配（稀疏向量）
    - 混合检索（结合两种向量的优势）
    """

    def __init__(self):
        """
        初始化Embedding服务

        从配置中读取：
        - model_path: 模型路径
        - dimension: 向量维度（默认768）
        """
        self.model_path = settings.EMBEDDING_MODEL
        self.dimension = settings.EMBEDDING_DIM
        self.dense_model = None  # 稠密向量模型（懒加载）
        self.sparse_vectorizer = None  # 稀疏向量化器（懒加载）

    def load_model(self):
        """
        加载本地embedding模型

        懒加载模式：首次调用encode时才加载模型，节省内存

        Raises:
            Exception: 模型加载失败时抛出异常
        """
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
        生成稠密向量（Dense Vector）

        使用 SentenceTransformer 模型将文本编码为固定维度的向量

        Args:
            texts: 单个文本或文本列表
            normalize_embeddings: 是否归一化向量（L2归一化，适合余弦相似度计算）

        Returns:
            - 输入单个文本：返回 List[float]（768维向量）
            - 输入文本列表：返回 List[List[float]]（多个768维向量）

        示例：
            >>> service = EmbeddingService()
            >>> vector = service.encode("北京故宫")  # 单个向量
            >>> vectors = service.encode(["故宫", "长城"])  # 多个向量
        """
        # 懒加载：首次调用时才加载模型
        if self.dense_model is None:
            self.load_model()

        # 处理输入格式：统一转换为列表
        if isinstance(texts, str):
            texts = [texts]
            single = True  # 标记是否为单个文本输入
        else:
            single = False

        # 生成向量（使用 SentenceTransformer 编码）
        embeddings = self.dense_model.encode(
            texts,
            convert_to_numpy=True,  # 返回numpy数组
            normalize_embeddings=normalize_embeddings,  # 是否L2归一化
            show_progress_bar=False  # 关闭进度条
        )

        # 转换为Python列表（便于JSON序列化）
        result = embeddings.tolist()

        # 如果输入是单个文本，返回单个向量（而不是列表）
        if single:
            return result[0]

        return result

    def encode_sparse(self, texts: List[str]) -> List[Dict[int, float]]:
        """
        生成稀疏向量（Sparse Vector，BM25风格）

        使用 TF-IDF + jieba 分词生成稀疏向量，适合关键词精确匹配

        工作原理：
        1. 使用 jieba 对中文文本分词
        2. 使用 TF-IDF 计算词项权重
        3. 转换为稀疏字典格式（只存储非零值）

        Args:
            texts: 文本列表

        Returns:
            稀疏向量列表，格式为 [{词项索引: 权重值}, ...]
            例如：[{12: 0.5, 45: 0.8, 67: 0.3}, ...]

        示例：
            >>> service = EmbeddingService()
            >>> sparse = service.encode_sparse(["北京故宫", "长城"])
            >>> # [{12: 0.5, 45: 0.8}, {23: 0.6, 67: 0.4}]
        """
        # 定义中文分词函数（使用jieba）
        def tokenize_chinese(text):
            return list(jieba.cut(text))

        # 懒加载：首次调用时初始化TF-IDF向量器
        if self.sparse_vectorizer is None:
            logger.info("[Embedding] Initializing sparse vectorizer")
            self.sparse_vectorizer = TfidfVectorizer(
                tokenizer=tokenize_chinese,  # 使用jieba分词
                max_features=10000,  # 最多保留10000个特征
                min_df=1,  # 最小文档频率
                token_pattern=None  # 不使用正则，因为已有tokenizer
            )
            # 拟合数据（构建词典）
            self.sparse_vectorizer.fit(texts)

        # 生成TF-IDF稀疏矩阵
        sparse_matrix = self.sparse_vectorizer.transform(texts)

        # 转换为稀疏字典格式（节省空间）
        sparse_vectors = []
        for i in range(sparse_matrix.shape[0]):
            row = sparse_matrix.getrow(i)  # 获取第i行
            sparse_dict = {
                int(idx): float(val)  # 词项索引 -> TF-IDF权重
                for idx, val in zip(row.indices, row.data)
                if val > 0  # 只保留非零值（稀疏性）
            }
            sparse_vectors.append(sparse_dict)

        logger.info(f"[Embedding] Generated {len(sparse_vectors)} sparse vectors")
        return sparse_vectors


# ==================== 单例模式 ====================
_embedding_service = None


def get_embedding_service() -> EmbeddingService:
    """
    获取Embedding服务单例

    使用单例模式避免重复加载模型，节省内存

    Returns:
        EmbeddingService: 全局唯一的Embedding服务实例

    示例：
        >>> from app.core.embedding_service import get_embedding_service
        >>> service = get_embedding_service()
        >>> vector = service.encode("测试文本")
    """
    global _embedding_service

    if _embedding_service is None:
        _embedding_service = EmbeddingService()

    return _embedding_service
