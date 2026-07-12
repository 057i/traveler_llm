"""
ChromaDB 鐠囧﹥鏌囬懘姘拱
"""
import chromadb
from pathlib import Path

# ChromaDB 鐠侯垰绶?chroma_path = "./data/vector_store"

print("=" * 80)
print("ChromaDB 鐠囧﹥鏌?)
print("=" * 80)

try:
    # 鏉╃偞甯?ChromaDB
    client = chromadb.PersistentClient(path=chroma_path)
    print(f"閴?ChromaDB 鏉╃偞甯撮幋鎰")
    print(f"   鐠侯垰绶? {chroma_path}")

    print(f"\n闂嗗棗鎮庨弫浼村櫤: {len(collections)}")

        print(f"\n闂嗗棗鎮庨崥宥囆? {col.name}")
        print(f"  ID: {col.id}")

        try:
            count = col.count()
            print(f"  閺佺増宓侀弶鈩冩殶: {count}")
            print(f"  count缁鐎? {type(count)}")

            # 鐏忔繆鐦懢宄板絿娑撯偓娴滄稒鏆熼幑?            if count > 0:
                results = col.peek(limit=1)
                print(f"  閺嶉攱婀伴弫鐗堝祦闁? {results.keys() if results else 'None'}")

        except Exception as e:
            print(f"  閴?闁挎瑨顕? {e}")
            print(f"  闁挎瑨顕ょ猾璇茬€? {type(e)}")
            import traceback
            traceback.print_exc()

    print("\n" + "=" * 80)
    print("鐠囧﹥鏌囩€瑰本鍨?)
    print("=" * 80)

except Exception as e:
    print(f"閴?ChromaDB 鏉╃偞甯存径杈Е: {e}")
    import traceback
    traceback.print_exc()
