from pymilvus import connections, utility
from loguru import logger

connections.connect(alias="default", host="localhost", port="19530")
logger.success("Connected to Milvus")

collections = utility.list_collections()
logger.info(f"Current collections: {collections}")

for coll_name in collections:
    utility.drop_collection(coll_name)
    logger.success(f"Dropped: {coll_name}")

logger.info(f"Remaining: {utility.list_collections()}")
print("Milvus cleared successfully")
