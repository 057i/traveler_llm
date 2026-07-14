from pymilvus import connections, utility, Collection
from loguru import logger

connections.connect(alias="default", host="localhost", port="19530")

collections = utility.list_collections()
logger.info(f"Collections: {collections}")

if "travel_destinations" in collections:
    coll = Collection("travel_destinations")
    coll.load()
    
    # 获取schema
    logger.info(f"Collection: {coll.name}")
    logger.info(f"Description: {coll.description}")
    
    # 列出所有字段
    for field in coll.schema.fields:
        logger.info(f"  - {field.name}: {field.dtype}")
    
    # 统计数量
    count = coll.num_entities
    logger.info(f"Total entities: {count}")
    
    print("Collection created successfully with extended fields!")
else:
    print("Collection not found")
