"""Milvus Client"""
from pymilvus import (
    connections,
    Collection,
    CollectionSchema,
    FieldSchema,
    DataType,
    utility
)
from typing import List, Dict, Any, Optional
from loguru import logger

from config.settings import settings


class MilvusClient:
    """Milvus vector database client"""

    def __init__(self):
        self.host = settings.MILVUS_HOST
        self.port = settings.MILVUS_PORT
        self.collection_name = settings.MILVUS_COLLECTION_NAME
        self.dimension = settings.EMBEDDING_DIM
        self.collection = None

    def connect(self):
        """Connect to Milvus"""
        try:
            connections.connect(
                alias="default",
                host=self.host,
                port=self.port
            )
            logger.success(f"Connected to Milvus: {self.host}:{self.port}")

            if utility.has_collection(self.collection_name):
                self.collection = Collection(self.collection_name)
                self.collection.load()
                logger.info(f"Loaded collection: {self.collection_name}")
            else:
                logger.warning(f"Collection {self.collection_name} does not exist")

        except Exception as e:
            logger.error(f"Failed to connect to Milvus: {e}")
            raise

    def create_collection(self):
        """Create collection if not exists"""
        if utility.has_collection(self.collection_name):
            logger.info(f"Collection {self.collection_name} already exists")
            return

        fields = [
            FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
            FieldSchema(name="destination_id", dtype=DataType.VARCHAR, max_length=256),
            FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=self.dimension),
            FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=65535)
        ]

        schema = CollectionSchema(fields=fields, description="Travel destinations")

        self.collection = Collection(name=self.collection_name, schema=schema)

        index_params = {
            "metric_type": "COSINE",
            "index_type": "IVF_FLAT",
            "params": {"nlist": 128}
        }

        self.collection.create_index(field_name="embedding", index_params=index_params)
        logger.success(f"Created collection: {self.collection_name}")

    def insert(self, data: List[Dict[str, Any]]) -> List[int]:
        """Insert vectors into collection"""
        if not self.collection:
            raise Exception("Collection not initialized")

        entities = [
            [item["destination_id"] for item in data],
            [item["embedding"] for item in data],
            [item["text"] for item in data]
        ]

        result = self.collection.insert(entities)
        self.collection.flush()

        logger.info(f"Inserted {len(data)} vectors")
        return result.primary_keys

    def search(
        self,
        query_vector: List[float],
        top_k: int = 10,
        filter_expr: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Search similar vectors"""
        if not self.collection:
            raise Exception("Collection not initialized")

        search_params = {"metric_type": "COSINE", "params": {"nprobe": 32}}

        results = self.collection.search(
            data=[query_vector],
            anns_field="embedding",
            param=search_params,
            limit=top_k,
            expr=filter_expr,
            output_fields=["destination_id", "text"]
        )

        output = []
        for hits in results:
            for hit in hits:
                output.append({
                    "id": hit.id,
                    "destination_id": hit.entity.get("destination_id"),
                    "text": hit.entity.get("text"),
                    "score": hit.score
                })

        logger.info(f"Found {len(output)} similar vectors")
        return output

    def delete(self, filter_expr: str):
        """Delete vectors by filter"""
        if not self.collection:
            raise Exception("Collection not initialized")

        self.collection.delete(filter_expr)
        logger.info(f"Deleted vectors with filter: {filter_expr}")

    def get_count(self) -> int:
        """Get number of entities in collection"""
        if not self.collection:
            return 0

        self.collection.flush()
        return self.collection.num_entities


_milvus_client = None


def get_milvus_client() -> MilvusClient:
    """Get singleton Milvus client instance"""
    global _milvus_client
    if _milvus_client is None:
        _milvus_client = MilvusClient()
        _milvus_client.connect()
    return _milvus_client
