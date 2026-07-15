"""
Milvus Hybrid Search Client with Rich Metadata

支持稀疏向量 + 稠密向量的混合检索，存储完整景点信息
"""
from pymilvus import (
    connections,
    Collection,
    CollectionSchema,
    FieldSchema,
    DataType,
    utility,
    AnnSearchRequest,
    RRFRanker
)
from typing import List, Dict, Any, Optional
from loguru import logger
from config.settings import settings


class MilvusHybridClient:
    """
    Milvus混合检索客户端

    功能：
    - 稠密向量检索（语义相似度，HNSW索引）
    - 稀疏向量检索（关键词匹配，倒排索引）
    - 混合检索（RRF融合）
    - 结构化筛选（预算、天数、标签等）
    - 完整元数据存储

    数据结构：
    - destination_id: 主键（景点唯一ID）
    - dense_vector: 768维稠密向量（bge-base-zh-v1.5）
    - sparse_vector: 稀疏向量（TF-IDF）
    - 元数据字段：name, province, city, category, description, rating
    - 扩展字段：estimated_budget, recommended_days, travel_type, tags, best_season

    索引类型：
    - 稠密向量：HNSW（高性能近似最近邻）
    - 稀疏向量：倒排索引（SPARSE_INVERTED_INDEX）
    - 标量字段：STL_SORT（支持范围筛选）
    """

    def __init__(self):
        self.host = settings.MILVUS_HOST
        self.port = settings.MILVUS_PORT
        self.collection_name = settings.MILVUS_COLLECTION_NAME
        self.dense_dim = settings.EMBEDDING_DIM  # 768
        self.collection = None

    def connect(self):
        """连接Milvus"""
        try:
            connections.connect(
                alias="default",
                host=self.host,
                port=self.port
            )
            logger.success(f"[Milvus] Connected to {self.host}:{self.port}")

            # 创建或加载collection
            if utility.has_collection(self.collection_name):
                self.collection = Collection(self.collection_name)
                logger.info(f"[Milvus] Loaded existing collection: {self.collection_name}")
            else:
                self._create_collection()

            # 加载collection到内存
            self.collection.load()
            logger.success(f"[Milvus] Collection loaded: {self.collection_name}")

        except Exception as e:
            logger.error(f"[Milvus] Connection failed: {e}")
            raise

    def _create_collection(self):
        """创建支持混合检索和丰富元数据的collection（HNSW索引）"""
        logger.info(f"[Milvus] Creating hybrid search collection with rich metadata: {self.collection_name}")

        # 定义字段
        fields = [
            # === 主键 ===
            FieldSchema(
                name="destination_id",
                dtype=DataType.VARCHAR,
                is_primary=True,
                max_length=200
            ),

            # === 向量字段 ===
            FieldSchema(
                name="dense_vector",
                dtype=DataType.FLOAT_VECTOR,
                dim=self.dense_dim,
                description="Dense embedding from bge-base-zh-v1.5"
            ),
            FieldSchema(
                name="sparse_vector",
                dtype=DataType.SPARSE_FLOAT_VECTOR,
                description="Sparse vector from BM25"
            ),

            # === 基本信息 ===
            FieldSchema(
                name="name",
                dtype=DataType.VARCHAR,
                max_length=200
            ),
            FieldSchema(
                name="province",
                dtype=DataType.VARCHAR,
                max_length=50
            ),
            FieldSchema(
                name="city",
                dtype=DataType.VARCHAR,
                max_length=50
            ),
            FieldSchema(
                name="category",
                dtype=DataType.VARCHAR,
                max_length=50
            ),
            FieldSchema(
                name="description",
                dtype=DataType.VARCHAR,
                max_length=2000
            ),

            # === 来源信息 ===
            FieldSchema(
                name="filename",
                dtype=DataType.VARCHAR,
                max_length=500,
                description="Source file name"
            ),

            # === 完整实体数据 ===
            FieldSchema(
                name="entity_json",
                dtype=DataType.VARCHAR,
                max_length=10000,
                description="Complete entity data in JSON format"
            ),

            # === 完整文本（用于检索和展示）===
            FieldSchema(
                name="full_text",
                dtype=DataType.VARCHAR,
                max_length=10000,
                description="Complete text for search and display"
            ),

            # === 评分 ===
            FieldSchema(
                name="rating",
                dtype=DataType.FLOAT
            ),

            # === 扩展字段（结构化筛选） ===
            FieldSchema(
                name="estimated_budget",
                dtype=DataType.INT32,
                description="Estimated budget per person (CNY)"
            ),
            FieldSchema(
                name="recommended_days",
                dtype=DataType.INT32,
                description="Recommended travel days"
            ),
            FieldSchema(
                name="travel_type",
                dtype=DataType.VARCHAR,
                max_length=50,
                description="Travel type category"
            ),
            FieldSchema(
                name="tags",
                dtype=DataType.ARRAY,
                element_type=DataType.VARCHAR,
                max_capacity=20,
                max_length=50,
                description="Feature tags"
            ),
            FieldSchema(
                name="best_season",
                dtype=DataType.ARRAY,
                element_type=DataType.VARCHAR,
                max_capacity=4,
                max_length=20,
                description="Best seasons to visit"
            )
        ]

        # 创建schema（禁用自动索引）
        schema = CollectionSchema(
            fields=fields,
            description="Travel destinations with hybrid search and complete metadata",
            enable_dynamic_field=True,
            auto_id=False
        )

        # 创建collection
        self.collection = Collection(
            name=self.collection_name,
            schema=schema
        )

        # ========== 创建HNSW索引（高性能） ==========
        from config.settings import settings

        dense_index_params = {
            "index_type": settings.MILVUS_INDEX_TYPE,  # "HNSW"
            "metric_type": "COSINE",
            "params": {
                "M": settings.MILVUS_INDEX_M,  # 16
                "efConstruction": settings.MILVUS_INDEX_EF_CONSTRUCTION  # 200
            }
        }
        self.collection.create_index(
            field_name="dense_vector",
            index_params=dense_index_params
        )
        logger.success(f"[Milvus] Created HNSW index: M={settings.MILVUS_INDEX_M}, efConstruction={settings.MILVUS_INDEX_EF_CONSTRUCTION}")

        # 创建索引 - 稀疏向量
        sparse_index_params = {
            "index_type": "SPARSE_INVERTED_INDEX",
            "metric_type": "IP"
        }
        self.collection.create_index(
            field_name="sparse_vector",
            index_params=sparse_index_params
        )

        # 创建标量字段索引（加速筛选）
        logger.info("[Milvus] Creating scalar indexes for filters...")

        self.collection.create_index(
            field_name="estimated_budget",
            index_params={"index_type": "STL_SORT"}
        )

        self.collection.create_index(
            field_name="recommended_days",
            index_params={"index_type": "STL_SORT"}
        )

        logger.success(f"[Milvus] Collection created with rich metadata support and scalar indexes")

    def insert(self, data: List[Dict[str, Any]]) -> List[str]:
        """
        插入混合向量数据和完整元数据

        Args:
            data: 数据列表，每项包含:
                - destination_id: 景点ID
                - dense_vector: 稠密向量 (768维)
                - sparse_vector: 稀疏向量 (dict)
                - name: 景点名称
                - province: 省份
                - city: 城市
                - category: 分类
                - description: 描述
                - filename: 来源文件名
                - entity_json: 完整实体JSON字符串
                - full_text: 完整文本
                - rating: 评分

        Returns:
            插入的主键列表
        """
        if not self.collection:
            raise Exception("Collection not initialized")

        # 准备数据
        entities = [
            [item["destination_id"] for item in data],
            [item["dense_vector"] for item in data],
            [item["sparse_vector"] for item in data],
            [item["name"] for item in data],
            [item.get("province", "") for item in data],
            [item.get("city", "") for item in data],
            [item.get("category", "") for item in data],
            [item.get("description", "") for item in data],
            [item.get("filename", "") for item in data],
            [item.get("entity_json", "{}") for item in data],
            [item["full_text"] for item in data],
            [item.get("rating", 0.0) for item in data],
            # 扩展字段（5个新字段）
            [item.get("estimated_budget", 200) for item in data],
            [item.get("recommended_days", 1) for item in data],
            [item.get("travel_type", "景点") for item in data],
            [item.get("tags", []) for item in data],
            [item.get("best_season", []) for item in data]
        ]

        # 插入数据
        result = self.collection.insert(entities)
        self.collection.flush()

        logger.info(f"[Milvus] Inserted {len(data)} entries with complete metadata")
        return result.primary_keys

    def hybrid_search(
        self,
        dense_vector: List[float],
        sparse_vector: Dict[int, float],
        top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """混合检索 (稠密 + 稀疏向量)"""
        if not self.collection:
            raise Exception("Collection not initialized")

        # 1. 稠密向量检索
        dense_search_params = {
            "metric_type": "COSINE",
            "params": {"nprobe": 10}
        }

        dense_req = AnnSearchRequest(
            data=[dense_vector],
            anns_field="dense_vector",
            param=dense_search_params,
            limit=top_k
        )

        # 2. 稀疏向量检索
        sparse_search_params = {
            "metric_type": "IP"
        }

        sparse_req = AnnSearchRequest(
            data=[sparse_vector],
            anns_field="sparse_vector",
            param=sparse_search_params,
            limit=top_k
        )

        # 3. RRF融合
        rerank = RRFRanker(k=60)

        # 4. 执行混合检索
        results = self.collection.hybrid_search(
            reqs=[dense_req, sparse_req],
            rerank=rerank,
            limit=top_k,
            output_fields=["destination_id", "name", "province", "city", "category", "description", "filename", "entity_json", "full_text", "rating"]
        )

        # 5. 格式化结果
        output = []
        for hits in results:
            for hit in hits:
                output.append({
                    "destination_id": hit.entity.get("destination_id"),
                    "name": hit.entity.get("name"),
                    "province": hit.entity.get("province"),
                    "city": hit.entity.get("city"),
                    "category": hit.entity.get("category"),
                    "description": hit.entity.get("description"),
                    "filename": hit.entity.get("filename"),
                    "entity_json": hit.entity.get("entity_json"),
                    "full_text": hit.entity.get("full_text"),
                    "rating": hit.entity.get("rating"),
                    "score": hit.score
                })

        logger.info(f"[Milvus] Hybrid search returned {len(output)} results")
        return output

    async def _search_dense(self, dense_vector: List[float], top_k: int = 20, expr: str = "") -> List[Dict[str, Any]]:
        """
        独立的稠密向量检索（HNSW索引）

        HNSW（Hierarchical Navigable Small World）优势：
        - 高速近似最近邻搜索
        - 支持大规模数据（百万级）
        - 准确率高（通过调整ef参数）

        Args:
            dense_vector: 稠密向量（768维）
            top_k: 返回结果数量
            expr: 过滤表达式（如：estimated_budget >= 100 && estimated_budget <= 500）

        Returns:
            检索结果列表，每项包含完整元数据和score
        """
        if not self.collection:
            raise Exception("Collection not initialized")

        try:
            from config.settings import settings

            # HNSW搜索参数
            dense_search_params = {
                "metric_type": "COSINE",
                "params": {"ef": settings.MILVUS_SEARCH_EF}  # 64，越大越准确
            }

            # 构建搜索参数
            search_params = {
                "data": [dense_vector],
                "anns_field": "dense_vector",
                "param": dense_search_params,
                "limit": top_k,
                "output_fields": [
                    "destination_id", "name", "province", "city", "category",
                    "description", "full_text", "rating",
                    "estimated_budget", "recommended_days", "travel_type",
                    "tags", "best_season"
                ]
            }

            # 如果有过滤表达式，添加expr
            if expr:
                search_params["expr"] = expr
                logger.info(f"[Milvus] Dense search with filter: {expr}")

            results = self.collection.search(**search_params)

            output = []
            for hits in results:
                for hit in hits:
                    output.append({
                        "destination_id": hit.entity.get("destination_id"),
                        "name": hit.entity.get("name"),
                        "province": hit.entity.get("province"),
                        "city": hit.entity.get("city"),
                        "category": hit.entity.get("category"),
                        "description": hit.entity.get("description"),
                        "content": hit.entity.get("full_text"),
                        "rating": hit.entity.get("rating"),
                        "estimated_budget": hit.entity.get("estimated_budget", 0),
                        "recommended_days": hit.entity.get("recommended_days", 1),
                        "travel_type": hit.entity.get("travel_type", ""),
                        "tags": list(hit.entity.get("tags", [])),  # 转换为list
                        "best_season": list(hit.entity.get("best_season", [])),  # 转换为list
                        "score": float(hit.score),
                        "source": "milvus_dense"
                    })

            logger.info(f"[Milvus] Dense search (HNSW) returned {len(output)} results")
            return output

        except Exception as e:
            logger.error(f"[Milvus] Dense search failed: {e}")
            import traceback
            traceback.print_exc()
            return []

    async def _search_sparse(self, query: str, top_k: int = 20, expr: str = "") -> List[Dict[str, Any]]:
        """
        独立的稀疏向量检索（真实稀疏向量搜索）

        工作流程：
        1. 使用jieba分词 + TF-IDF生成查询的稀疏向量
        2. 使用倒排索引进行稀疏向量检索（anns_field="sparse_vector"）
        3. 如果失败，降级为关键词匹配

        优势：
        - 精确匹配关键词
        - 补充语义检索的不足
        - 适合专有名词查询

        Args:
            query: 查询文本（如："北京故宫"）
            top_k: 返回结果数量
            expr: 过滤表达式（可选）

        Returns:
            检索结果列表
        """
        if not self.collection:
            raise Exception("Collection not initialized")

        try:
            # 1. 生成稀疏向量
            from app.core.embedding_service import get_embedding_service
            embedding_service = get_embedding_service()

            # 生成稀疏向量（TF-IDF）
            sparse_vectors = embedding_service.encode_sparse([query])
            if not sparse_vectors or not sparse_vectors[0]:
                logger.warning(f"[Milvus] No sparse vector generated, fallback to keyword matching")
                return await self._search_sparse_fallback(query, top_k)

            sparse_vector = sparse_vectors[0]
            logger.info(f"[Milvus] Generated sparse vector with {len(sparse_vector)} non-zero elements")

            # 2. 使用稀疏向量搜索（anns_field）
            sparse_search_params = {
                "metric_type": "IP",  # 内积（适合稀疏向量）
                "params": {}
            }

            # 构建搜索参数
            search_params = {
                "data": [sparse_vector],
                "anns_field": "sparse_vector",
                "param": sparse_search_params,
                "limit": top_k,
                "output_fields": [
                    "destination_id", "name", "province", "city", "category",
                    "description", "full_text", "rating",
                    "estimated_budget", "recommended_days", "travel_type",
                    "tags", "best_season"
                ]
            }

            # 如果有过滤表达式，添加expr
            if expr:
                search_params["expr"] = expr
                logger.info(f"[Milvus] Sparse search with filter: {expr}")

            results = self.collection.search(**search_params)

            # 3. 格式化结果
            output = []
            for hits in results:
                for hit in hits:
                    output.append({
                        "destination_id": hit.entity.get("destination_id"),
                        "name": hit.entity.get("name"),
                        "province": hit.entity.get("province"),
                        "city": hit.entity.get("city"),
                        "category": hit.entity.get("category"),
                        "description": hit.entity.get("description"),
                        "content": hit.entity.get("full_text"),
                        "rating": hit.entity.get("rating"),
                        "estimated_budget": hit.entity.get("estimated_budget", 0),
                        "recommended_days": hit.entity.get("recommended_days", 1),
                        "travel_type": hit.entity.get("travel_type", ""),
                        "tags": list(hit.entity.get("tags", [])),  # 转换为list
                        "best_season": list(hit.entity.get("best_season", [])),  # 转换为list
                        "score": float(hit.score),
                        "source": "milvus_sparse"
                    })

            logger.info(f"[Milvus] Sparse search (ANNS) returned {len(output)} results")

            # 如果结果少，记录警告但直接返回（不再fallback到query）
            if len(output) < top_k // 2:
                logger.warning(f"[Milvus] Sparse ANNS returned only {len(output)} results (expected ~{top_k})")
                logger.warning(f"[Milvus] Fallback disabled due to query issue")

            return output

        except Exception as e:
            logger.warning(f"[Milvus] Sparse ANNS search failed: {e}, fallback to keyword matching")
            # 降级为关键词匹配
            return await self._search_sparse_fallback(query, top_k)

    async def _search_sparse_fallback(self, query: str, top_k: int = 20) -> List[Dict[str, Any]]:
        """
        稀疏检索降级方案（关键词匹配）

        当真实稀疏向量搜索失败时使用
        """
        try:
            import jieba

            # 分词
            keywords = list(jieba.cut(query))
            logger.info(f"[Milvus] Sparse fallback keywords: {keywords}")

            # 查询所有数据
            results = self.collection.query(
                expr="",
                output_fields=["destination_id", "name", "province", "city", "category", "description", "full_text", "rating"],
                limit=top_k * 3
            )

            # 关键词匹配评分
            scored_results = []
            for result in results:
                text = (
                    result.get("name", "") + " " +
                    result.get("description", "") + " " +
                    result.get("full_text", "")
                )

                # 计算匹配分数
                match_count = sum(1 for kw in keywords if kw in text)
                if match_count > 0:
                    score = match_count / len(keywords)
                    scored_results.append({
                        "destination_id": result.get("destination_id"),
                        "name": result.get("name"),
                        "province": result.get("province"),
                        "city": result.get("city"),
                        "category": result.get("category"),
                        "description": result.get("description"),
                        "content": result.get("full_text"),
                        "rating": result.get("rating"),
                        "score": float(score),
                        "source": "milvus_sparse_fallback"
                    })

            # 按分数排序
            scored_results.sort(key=lambda x: x["score"], reverse=True)
            output = scored_results[:top_k]

            logger.info(f"[Milvus] Sparse fallback returned {len(output)} results")
            return output

        except Exception as e:
            logger.error(f"[Milvus] Sparse fallback failed: {e}")
            return []

    def delete(self, filter_expr: str):
        """删除向量"""
        if not self.collection:
            raise Exception("Collection not initialized")

        self.collection.delete(filter_expr)
        logger.info(f"[Milvus] Deleted with filter: {filter_expr}")

    def get_count(self) -> int:
        """获取向量数量"""
        if not self.collection:
            return 0

        self.collection.flush()
        return self.collection.num_entities


# 单例
_milvus_hybrid_client = None


def get_milvus_hybrid_client() -> MilvusHybridClient:
    """获取Milvus混合检索客户端单例"""
    global _milvus_hybrid_client

    if _milvus_hybrid_client is None:
        _milvus_hybrid_client = MilvusHybridClient()
        _milvus_hybrid_client.connect()

    return _milvus_hybrid_client
