"""
閺屻儳婀?ChromaDB 娑擃厾娈戦弫鐗堝祦
"""
import chromadb

# 鏉╃偞甯撮崚鐗堟殶閹诡喖绨?client = chromadb.PersistentClient(path='./data/vector_store')
collection = client.get_collection('travel_destinations')

print(f'閹粯鏆熼幑顕€鍣? {collection.count()}')
print('\n閺佺増宓侀崚妤勩€?')
print('=' * 80)


for i, meta in enumerate(results['metadatas'], 1):
    name = meta.get('name', '閺堫亞鐓?)
    location = meta.get('location', '閺堫亞鐓?)
    rating = meta.get('rating', 0)
    print(f'{i}. {name} - {location} (鐠囧嫬鍨? {rating})')
