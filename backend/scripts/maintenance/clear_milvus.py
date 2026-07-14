"""
清空Milvus Collection
"""
from pymilvus import connections, utility, Collection
from loguru import logger

try:
    # 连接Milvus
    connections.connect(
        alias="default",
        host="localhost",
        port="19530"
    )
    logger.success("Connected to Milvus")
    
    # 获取Collection名称
    collection_name = "travel_destinations_hybrid"
    
    # 检查是否存在
    if utility.has_collection(collection_name):
        # 删除Collection
        utility.drop_collection(collection_name)
        logger.success(f"Dropped collection: {collection_name}")
    else:
        logger.info(f"Collection {collection_name} does not exist")
    
    # 列出所有Collection
    collections = utility.list_collections()
    logger.info(f"Remaining collections: {collections}")
    
    print("✅ Milvus清空完成")
    
except Exception as e:
    print(f"❌ 清空Milvus失败: {e}")
    import traceback
    traceback.print_exc()
