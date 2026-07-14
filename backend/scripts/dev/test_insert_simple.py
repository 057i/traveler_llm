"""
测试Milvus插入 - 直接测试字段匹配
"""
from pymilvus import connections, Collection
from loguru import logger
import numpy as np

connections.connect(alias="default", host="localhost", port="19530")

coll = Collection("travel_destinations")
coll.load()

logger.info(f"Collection: {coll.name}")
logger.info(f"Fields count: {len(coll.schema.fields)}")

# 列出所有字段
for field in coll.schema.fields:
    logger.info(f"  - {field.name}: {field.dtype}")

# 创建测试数据
dense_vector = np.random.randn(768).tolist()
sparse_vector = {0: 0.5, 1: 0.3, 2: 0.8}

test_data = [{
    "destination_id": "test_001",
    "dense_vector": dense_vector,
    "sparse_vector": sparse_vector,
    "name": "测试景点",
    "province": "江西省",
    "city": "上饶市",
    "category": "自然风光",
    "description": "测试",
    "filename": "test.json",
    "entity_json": "{}",
    "full_text": "测试文本",
    "rating": 4.5,
    "estimated_budget": 300,
    "recommended_days": 2,
    "travel_type": "自然风光",
    "tags": ["测试"],
    "best_season": ["春"]
}]

logger.info(f"Test data fields: {len(test_data[0])}")
for key in test_data[0].keys():
    val = test_data[0][key]
    logger.info(f"  - {key}: {type(val).__name__}")

try:
    result = coll.insert(test_data)
    logger.success(f"Insert success! Count: {result.insert_count}")
    print("SUCCESS!")
except Exception as e:
    logger.error(f"Insert failed: {e}")
    print(f"FAILED: {e}")
