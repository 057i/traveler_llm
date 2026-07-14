"""
测试Milvus插入 - 验证字段是否匹配
"""
from app.core.milvus_hybrid_client import get_milvus_hybrid_client
from app.core.embedding_service import get_embedding_service
from loguru import logger
import sys

try:
    # 初始化客户端
    milvus = get_milvus_hybrid_client()
    embedding = get_embedding_service()
    
    logger.info("Clients initialized")
    
    # 准备测试数据
    test_text = "三清山位于江西省上饶市，是世界自然遗产"
    
    # 生成向量
    dense_vector = embedding.encode(test_text, normalize_embeddings=True)
    sparse_vectors = embedding.encode_sparse([test_text])
    sparse_vector = sparse_vectors[0] if sparse_vectors else {}
    
    logger.info(f"Vectors generated: dense={len(dense_vector)}, sparse={len(sparse_vector)}")
    
    # 构造数据（完整17个字段）
    test_data = [{
        "destination_id": "test_001",
        "dense_vector": dense_vector.tolist(),
        "sparse_vector": sparse_vector,
        "name": "三清山测试",
        "province": "江西省",
        "city": "上饶市",
        "category": "自然风光",
        "description": "测试景点",
        "filename": "test.json",
        "entity_json": "{}",
        "full_text": test_text,
        "rating": 4.5,
        "estimated_budget": 300,
        "recommended_days": 2,
        "travel_type": "自然风光",
        "tags": ["测试", "自然"],
        "best_season": ["春", "秋"]
    }]
    
    logger.info(f"Test data prepared with {len(test_data[0])} fields")
    
    # 列出所有字段
    logger.info("Fields in test data:")
    for key in test_data[0].keys():
        logger.info(f"  - {key}: {type(test_data[0][key]).__name__}")
    
    # 尝试插入
    logger.info("Attempting to insert...")
    result = milvus.insert(test_data)
    
    logger.success(f"Insert successful! IDs: {result}")
    print("Test passed! Data structure is correct.")
    
except Exception as e:
    logger.error(f"Insert failed: {e}")
    import traceback
    traceback.print_exc()
    print(f"Test failed: {e}")
    sys.exit(1)
