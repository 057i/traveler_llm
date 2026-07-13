from pymilvus import Collection, connections

print("Connecting to Milvus...")
connections.connect(host="localhost", port=19530)
collection = Collection("travel_destinations")

print(f"Current entities: {collection.num_entities}")

print("\nFlushing collection...")
collection.flush()

print("Reloading collection...")
collection.load()

print("\nTesting query...")
results = collection.query(expr="", output_fields=["name"], limit=3)
print(f"Query returned {len(results)} results")

if results:
    print("\n=== SUCCESS: Query is now working! ===")
    print("Sample results:")
    for i, r in enumerate(results, 1):
        print(f"  {i}. {r.get('name')}")
else:
    print("\n=== FAILED: Query still returns 0 ===")
    print("May need to restart Milvus service")

connections.disconnect("default")
print("\nDone!")
