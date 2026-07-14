from pymilvus import connections, Collection
from loguru import logger

connections.connect(alias="default", host="localhost", port="19530")

coll = Collection("travel_destinations")
coll.load()

# 查询数量
count = coll.num_entities
logger.info(f"Total entities: {count}")

# 查询前5条数据
if count > 0:
    results = coll.query(
        expr="",
        output_fields=["name", "city", "estimated_budget", "recommended_days", "travel_type", "tags", "best_season"],
        limit=5
    )
    
    for r in results:
        logger.info(f"Name: {r.get('name')}")
        logger.info(f"  City: {r.get('city')}")
        logger.info(f"  Budget: {r.get('estimated_budget')}")
        logger.info(f"  Days: {r.get('recommended_days')}")
        logger.info(f"  Type: {r.get('travel_type')}")
        logger.info(f"  Tags: {r.get('tags')}")
        logger.info(f"  Season: {r.get('best_season')}")
        logger.info("---")
    
    print(f"Data uploaded successfully! Total: {count} entities")
else:
    print("No data found!")
