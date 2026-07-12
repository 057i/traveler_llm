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
    """Milvus混合检索客户端 - 支持稀疏+稠密向量 + 完整元数据"""

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
        """创建支持混合检索和丰富元数据的collection"""
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

        # 创建索引 - 稠密向量
        dense_index_params = {
            "index_type": "IVF_FLAT",
            "metric_type": "COSINE",
            "params": {"nlist": 128}
        }
        self.collection.create_index(
            field_name="dense_vector",
            index_params=dense_index_params
        )

        # 创建索引 - 稀疏向量
        sparse_index_params = {
            "index_type": "SPARSE_INVERTED_INDEX",
            "metric_type": "IP"
        }
        self.collection.create_index(
            field_name="sparse_vector",
            index_params=sparse_index_params
        )

        logger.success(f"[Milvus] Collection created with rich metadata support")

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
            [item.get("rating", 0.0) for item in data]
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
