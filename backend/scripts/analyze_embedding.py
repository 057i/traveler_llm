import sys
sys.path.insert(0, 'E:/婢堆勀侀崹瀣磻閸?娴狅絿鐖?缂冩垹鐝?travel_proj/backend')

from app.core.milvus_rag_client import get_rag_engine
from app.models.schemas import QueryRequest, Destination, Season, TravelType

print('=' * 80)
print('閸掑棙鐎紼mbedding娑撯偓閼峰瓨鈧囨６妫?)
print('=' * 80)

rag_engine = get_rag_engine()

print('-' * 80)
collection = rag_engine.vectorstore._collection
sample = collection.get(limit=1, include=['documents', 'metadatas'])

if sample['documents']:
    stored_doc = sample['documents'][0]
    print('鐎涙ê鍋嶉惃鍕瀮濡楋絿銇氭笟?')
    print(stored_doc)
    print(f'\n閺傚洦銆傞梹鍨: {len(stored_doc)} 鐎涙顑?)

print('-' * 80)
test_dest = Destination(
    name="娑撳绔荤仦?,
    location="濮圭喕銈块惇浣风瑐妤楄泛绔?,
    description="娑撳绔荤仦杈ㄦЦ闁挻鏆€閸氬秴鍖楅敍灞间簰婵傚洤鍢查幀顏嗙叾閵嗕椒绨ù閿嬫）閸戦缚鎲茬粔鑸偓?,
    tags=["閼奉亞鍔ф搴″帨", "闁挻鏆€閺傚洤瀵?],
    best_season=[Season.SPRING, Season.AUTUMN],
    budget_range=[800, 2000],
    suitable_for=[TravelType.FAMILY],
    features=["娑撴牜鏅懛顏嗗姧闁ぞ楠?, "婵傚洤鍢查幀顏嗙叾"],
    rating=4.8,
    image_url="https://example.com/test.jpg"
)

formatted = rag_engine._format_destination_text(test_dest)
print('閺嶇厧绱￠崠鏍ф倵閻ㄥ嫭鏋冮張?')
print(formatted)
print(f'\n閺嶇厧绱￠崠鏍ㄦ瀮閺堫剟鏆辨惔? {len(formatted)} 鐎涙顑?)

print('-' * 80)
query_request = QueryRequest(query='娑撳绔荤仦杈ㄦ⒕濞撳憡鏁鹃悾?)
query_text = rag_engine._build_query_text(query_request)
print(f'閺屻儴顕楅弬鍥ㄦ拱: "{query_text}"')
print(f'閺屻儴顕楅弬鍥ㄦ拱闂€鍨: {len(query_text)} 鐎涙顑?)

print('-' * 80)
print('鐎涙ê鍋嶉惃鍕瀮濡楋絾鐗稿?')
print('  - 閸栧懎鎯堢€瑰本鏆ｉ惃鍕珯閻愰€涗繆閹垽绱欓崥宥囆為妴浣风秴缂冾喓鈧焦寮挎潻鑸偓浣圭垼缁涘墽鐡戦敍?)
print('  - 閺傚洦銆傚鍫ユ毐閿涘奔淇婇幁顖欒荡鐎?)
print('')
print('閺屻儴顕楅惃鍕瀮閺堫剚鐗稿?')
print('  - 閸欘亝婀侀悽銊﹀煕鏉堟挸鍙嗛惃鍕叀鐠囥垼顕㈤崣?)
print('  - 閺傚洦婀板鍫㈢叚')
print('')
print('缂佹捁顔?')
print('  閳?鐎涙ê鍋嶉崪灞剧叀鐠囥垻娈戦弬鍥ㄦ拱閺嶇厧绱℃稉宥呭爱闁板稄绱?)
print('  閳?鐎涙ê鍋嶉弮鍓佹暏閻ㄥ嫭妲哥紒鎾寸€崠鏍畱鐠囷妇绮忔穱鈩冧紖')
print('  閳?閺屻儴顕楅弮鍓佹暏閻ㄥ嫭妲哥粻鈧惌顓犳畱閻劍鍩涢梻顕€顣?)
print('  閳?鐎佃壈鍤ч崥鎴﹀櫤缁屾椽妫挎稉顓＄獩缁傛槒绶濇潻婊愮礉閻╅晲鎶€鎼达缚缍?)

print('-' * 80)

test_queries = [
    '娑撳绔荤仦杈ㄦ⒕濞撳憡鏁鹃悾?,
    '娑撳绔荤仦?,
    '濮圭喕銈块惇浣风瑐妤楄泛绔?娑撳绔荤仦?閼奉亞鍔ф搴″帨 闁挻鏆€閺傚洤瀵?,
]

for query in test_queries:
    docs = rag_engine.vectorstore.similarity_search_with_score(query, k=1)
    if docs:
        doc, score = docs[0]
        similarity = 1 - score if score < 1 else 1 / (1 + score)
        name = doc.metadata.get('name', 'N/A')
        print(f'\n閺屻儴顕? "{query}"')
        print(f'  閳?閺堚偓娴ｅ啿灏柊? {name}')
        print(f'  閳?閻╅晲鎶€鎼? {similarity:.3f}')
        print(f'  閳?閺勵垰鎯?0.7: {"閴? if similarity >= 0.7 else "閴?}')

print('\n' + '=' * 80)
print('瀵ら缚顔? 闂勫秳缍嗛惄闀愭妧鎼达箓妲囬崐鐓庡煂 0.3-0.5 閹存牔绱崠鏍ㄧ叀鐠囥垺鏋冮張顒佺€?)
print('=' * 80)
