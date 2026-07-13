from pymilvus import Collection, connections, utility

connections.connect(host="localhost", port=19530)

# 检查collection信息
collection_name = "travel_destinations"
print(f"Checking collection: {collection_name}")
print(f"Collection exists: {utility.has_collection(collection_name)}")

if utility.has_collection(collection_name):
    collection = Collection(collection_name)
    print(f"Num entities: {collection.num_entities}")
    
    # 检查是否加载
    print(f"Loading collection...")
    collection.load()
    
    # 尝试简单查询
    print("Attempting query with limit=1...")
    try:
        results = collection.query(expr="", output_fields=["name"], limit=1)
        print(f"Query returned {len(results)} results")
        if results:
            print(f"First result: {results[0]}")
    except Exception as e:
        print(f"Query failed: {e}")
    
    # 尝试搜索
    print("\nAttempting search...")
    try:
        # 生成一个随机向量进行测试搜索
        import numpy as np
        test_vector = np.random.rand(768).tolist()
        
        search_results = collection.search(
            data=[test_vector],
            anns_field="dense_vector",
            param={"metric_type": "COSINE", "params": {"ef": 64}},
            limit=1,
            output_fields=["name"]
        )
        print(f"Search returned {len(search_results)} results")
        if search_results and len(search_results[0]) > 0:
            print(f"First search result: {search_results[0][0].entity.get('name')}")
    except Exception as e:
        print(f"Search failed: {e}")

connections.disconnect("default")
