"""
閹烘帗鐓ilvus濞ｅ嘲鎮庡Λ鈧槐銏犲瀻閺侀缍嗛惃鍕６妫?"""
import sys
sys.path.insert(0, '.')

from pymilvus import connections, Collection
from config.settings import settings
from app.core.milvus_rag_client import get_rag_engine
from app.models.schemas import QueryRequest

# 鏉╃偞甯碝ilvus
connections.connect(host=settings.MILVUS_HOST, port=settings.MILVUS_PORT)
col = Collection('travel_destinations')

print("=" * 80)
print("闂傤噣顣介幒鎺撶叀閿涙矮璐熸禒鈧稊?鐟楄儻妫岄弮鍛埗'閹兼粎鍌ㄩ崚鍡樻殶鏉╂瑤绠炴担搴吹")
print("=" * 80)

print("-" * 80)
results = col.query(
    expr='id >= 0',
    output_fields=['name', 'location', 'description'],
    limit=88
)

xizang_destinations = []
for r in results:
    location = r.get('location', '')
    name = r.get('name', '')
    if '鐟楄儻妫? in location or '鐟楄儻妫? in name or '閹峰鎯? in location:
        xizang_destinations.append(r)

print(f"OK 閹垫儳鍩?{len(xizang_destinations)} 娑擃亣銈块挊蹇曟祲閸忚櫕娅欓悙?)
for i, dest in enumerate(xizang_destinations[:5], 1):
    print(f"   {i}. {dest['name']} - {dest['location']}")

print("-" * 80)
rag_engine = get_rag_engine()
query = QueryRequest(query='鐟楄儻妫岄弮鍛埗')

results = rag_engine.search(query, top_k=10)
print(f"OK 鏉╂柨娲?{len(results)} 娑擃亞绮ㄩ弸娣簄")

for i, r in enumerate(results[:5], 1):
    print(f"{i}. {r.name}")
    print(f"   娴ｅ秶鐤? {r.destination.location}")
    print(f"   閸掑棙鏆? {r.score:.6f}")
    print(f"   閸樼喎娲? {r.reason}")
    has_xizang = '鐟楄儻妫? in r.destination.location or '鐟楄儻妫? in r.name
    print(f"   閺勵垰鎯佺憲鑳: {'[YES]' if has_xizang else '[NO]'}")
    print()

print("\n[濮濄儵顎?] 閸掑棙鐎絉RF閸掑棙鏆熺拋锛勭暬闁槒绶?)
print("-" * 80)
k = 60
alpha = 0.5

print(f"RRF閸欏倹鏆? k={k}, alpha={alpha}")
print(f"\nRRF閸忣剙绱? score = alpha * 1/(k+rank_dense) + (1-alpha) * 1/(k+rank_sparse)")
print(f"\n閻炲棜顔戦崚鍡樻殶閼煎啫娲?")
print(f"  缁?閸?娑撱倓閲滃Λ鈧槐銏ゅ厴缁?): {alpha * 1/(k+1) + (1-alpha) * 1/(k+1):.6f}")
print(f"  缁?閸?娴犲懐顭嗙€靛棛顑?):     {alpha * 1/(k+1):.6f}")
print(f"  缁?0閸?娑撱倓閲滃Λ鈧槐銏ゅ厴缁?0): {alpha * 1/(k+10) + (1-alpha) * 1/(k+10):.6f}")

print("-" * 80)
print("[X] 闂傤噣顣?: RRF閸掑棙鏆熸径顏勭毈")
print("   - 閸楀厖濞囬幒鎺戞倳缁?閿涘苯鍨庨弫棰佺瘍閸欘亝婀?~0.016")
print("   - 鏉╂瑦妲搁崶鐘辫礋k=60婢额亜銇囬敍灞筋嚤閼?1/(k+rank) 閻ㄥ嫬鈧厧绶㈢亸?)
print()
print("[X] 闂傤噣顣?: RRF韫囩晫鏆愭禍鍡楀斧婵娴夋导鐓庡")
print("   - 缁嬬姴鐦戦崥鎴﹀櫤閸欘垵鍏橀張?.95閻ㄥ嫰鐝惄闀愭妧鎼?)
print("   - 娴ｅ摏RF閸欘亞婀呴幒鎺戞倳閿涘奔娑径鍙樼啊閻╅晲鎶€鎼达缚淇婇幁?)
print()
print("[X] 闂傤噣顣?: 婵″倹鐏夐弫鐗堝祦娑擃厽鐥呴張澶庛偪閽樺繑娅欓悙?)
print(f"   - 瑜版挸澧犻崣顏呮箒 {len(xizang_destinations)} 娑擃亣銈块挊蹇旀珯閻?)
print("   - 婵″倹鐏夋稉?閿涘苯鍨弮鐘崇《鏉╂柨娲栫划鍓р€橀崠褰掑帳")

print("-" * 80)
print("閺傝顢?: 闂勫秳缍哛RF閻ㄥ埍閸?)
print("   - 娴犲窂=60閺€閫涜礋k=10")
print("   - 缁?閸氬秴鍨庨弫? 1/(10+1) 閳?0.091 (閹绘劕宕?閸?")
print()
print("閺傝顢?: 缂佹挸鎮庨崢鐔奉潗閸掑棙鏆?)
print("   - RRF閸掑棙鏆?* 閸樼喎顫愰獮鍐叉綆閻╅晲鎶€鎼?)
print("   - 娓氬顩? 0.016 * 0.85 = 0.0136")
print()
print("閺傝顢?: 娴ｈ法鏁ら崝鐘虫綀楠炲啿娼庨弴澶稿敩RRF")
print("   - score = alpha * dense_score + (1-alpha) * sparse_score")
print("   - 娣囨繄鏆€閸樼喎顫愰惄闀愭妧鎼达缚淇婇幁?)

print("\n" + "=" * 80)
print("閹烘帗鐓＄€瑰本鍨氶敍?)
print("=" * 80)
