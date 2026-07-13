from pymilvus import Collection, connections
import sys

try:
    # 连接Milvus
    connections.connect(host="localhost", port=19530)
    collection = Collection("travel_destinations")
    collection.load()
    
    # 检查总数
    total = collection.num_entities
    print(f"总数据量: {total}条")
    
    # 查询一条数据
    if total > 0:
        result = collection.query(
            expr="",
            output_fields=["name", "dense_vector", "sparse_vector"],
            limit=1
        )
        
        if result:
            print(f"示例数据: {result[0].get('name')}")
            print(f"稠密向量: {'有' if result[0].get('dense_vector') else '无'}")
            print(f"稀疏向量: {'有' if result[0].get('sparse_vector') else '无'}")
        else:
            print("❌ 无法查询数据")
    else:
        print("❌ 数据库为空！")
        
    connections.disconnect("default")
    
except Exception as e:
    print(f"❌ 错误: {e}")
    sys.exit(1)
