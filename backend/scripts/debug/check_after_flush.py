from pymilvus import connections, Collection

connections.connect(alias="default", host="localhost", port="19530")
coll = Collection("travel_destinations")

# Flush确保数据持久化
print("Flushing collection...")
coll.flush()
print("Flush complete")

# 重新加载
coll.load()

# 查询数量
count = coll.num_entities
print(f"Total entities: {count}")

if count > 0:
    results = coll.query(
        expr="",
        output_fields=["name", "city", "estimated_budget"],
        limit=5
    )
    for r in results:
        print(f"  - {r.get('name')} ({r.get('city')}) - ¥{r.get('estimated_budget')}")
