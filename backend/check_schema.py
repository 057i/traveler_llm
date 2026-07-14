from pymilvus import connections, Collection, utility
from loguru import logger

connections.connect(alias="default", host="localhost", port="19530")

collections = utility.list_collections()
logger.info(f"All collections: {collections}")

if "travel_destinations" in collections:
    coll = Collection("travel_destinations")
    coll.load()
    
    logger.info(f"Collection: {coll.name}")
    logger.info(f"Total fields: {len(coll.schema.fields)}")
    
    print("\nFields in collection:")
    for i, field in enumerate(coll.schema.fields, 1):
        print(f"  {i}. {field.name}: {field.dtype}")
    
    print(f"\nProblem: Collection has {len(coll.schema.fields)} fields")
    print("Expected: 17 fields (12 original + 5 new)")
    
    if len(coll.schema.fields) < 17:
        print("\nSolution: Must delete and recreate collection!")
else:
    print("Collection not found")
