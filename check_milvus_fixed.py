from pymilvus import Collection, connections
import sys

try:
    # 连接Milvus
    connections.connect(host="localhost", port=19530)
    collection = Collection("travel_destinations")
    collection.load()

    # 检查总数
    total = collection.num_entities
    print(f"Total data: {total}")

    # 查询一条数据
    if total > 0:
        result = collection.query(
            expr="",
            output_fields=["name", "dense_vector", "sparse_vector"],
            limit=1
        )

        if result:
            print(f"Sample data: {result[0].get('name')}")
            has_dense = result[0].get('dense_vector') is not None
            has_sparse = result[0].get('sparse_vector') is not None
            print(f"Dense vector: {'YES' if has_dense else 'NO'}")
            print(f"Sparse vector: {'YES' if has_sparse else 'NO'}")

            if has_dense:
                print(f"Dense vector dim: {len(result[0].get('dense_vector'))}")
            if has_sparse:
                sparse = result[0].get('sparse_vector')
                if isinstance(sparse, dict):
                    print(f"Sparse vector elements: {len(sparse)}")
                else:
                    print(f"Sparse vector type: {type(sparse)}")
        else:
            print("ERROR: Cannot query data")
    else:
        print("ERROR: Database is empty!")

    connections.disconnect("default")

except Exception as e:
    print(f"ERROR: {e}")
    sys.exit(1)
