"""
鐠囧﹥鏌囬幖婊呭偍"鐟楄儻妫?鏉╂柨娲栨稉宥囨祲閸忓磭绮ㄩ弸婊呮畱闂傤噣顣?"""
import requests
import json

print("=" * 80)
print("鐠囧﹥鏌囬幖婊呭偍闂傤噣顣介敍姘炽偪閽?-> 婢垛晠妫仦鍗炵盀")
print("=" * 80)

print("\n[濞村鐦?] 閹兼粎鍌?鐟楄儻妫?")
print("-" * 80)

body = {
    "query": {
        "query": "鐟楄儻妫?
    },
    "models": ["rag"],
    "weights": {"rag": 1.0}
}

try:
    response = requests.post(
        "http://localhost:8000/api/rrf-recommend/fuse_with_diversity",
        params={"alpha": 0.7, "top_k": 5},
        json=body,
        timeout=30
    )

    if response.status_code == 200:
        data = response.json()
        results = data.get('results', [])

        print(f"\n鏉╂柨娲栫紒鎾寸亯閺? {len(results)}")

        for i, result in enumerate(results, 1):
            print(f"\n[{i}] {result.get('name')}")
            print(f"  娴ｅ秶鐤? {result['destination'].get('location')}")
            print(f"  閸掑棙鏆? {result.get('score'):.4f}")
            print(f"  閻炲棛鏁? {result.get('reason')}")
            print(f"  閹诲繗鍫? {result['destination'].get('description')[:50]}...")

    else:
        print(f"\n鐠囬攱鐪版径杈Е: {response.status_code}")

except Exception as e:
    print(f"\n闁挎瑨顕? {e}")

print("[濞村鐦?] 閹兼粎鍌?娑撳绔荤仦?閿涘牆顕悡褏绮嶉敍?)
print("-" * 80)

body2 = {
    "query": {
        "query": "娑撳绔荤仦?
    },
    "models": ["rag"],
    "weights": {"rag": 1.0}
}

try:
    response = requests.post(
        "http://localhost:8000/api/rrf-recommend/fuse_with_diversity",
        params={"alpha": 0.7, "top_k": 5},
        json=body2,
        timeout=30
    )

    if response.status_code == 200:
        data = response.json()
        results = data.get('results', [])

        print(f"\n鏉╂柨娲栫紒鎾寸亯閺? {len(results)}")

        for i, result in enumerate(results, 1):
            print(f"\n[{i}] {result.get('name')}")
            print(f"  娴ｅ秶鐤? {result['destination'].get('location')}")
            print(f"  閸掑棙鏆? {result.get('score'):.4f}")
            print(f"  閻炲棛鏁? {result.get('reason')}")

    else:
        print(f"\n鐠囬攱鐪版径杈Е: {response.status_code}")

except Exception as e:
    print(f"\n闁挎瑨顕? {e}")

print("\n" + "=" * 80)
print("鐠囧﹥鏌囬崚鍡樼€?)
print("=" * 80)

print("""
閸欘垵鍏橀惃鍕斧閸ョ媴绱?1. 閺佺増宓佹惔鎾茶厬濞屸剝婀佺憲鑳閺咁垳鍋?-> 鏉╂柨娲栭惄闀愭妧鎼达附娓舵妯兼畱缂佹挻鐏?2. 閸氭垿鍣哄Λ鈧槐銏㈡祲娴肩厧瀹抽梼鍫濃偓鐓庛亰娴?-> 閸楀厖濞囨稉宥囨祲閸忓厖绡冩潻鏂挎礀
3. 缁嬧偓閻ゅ繐鎮滈柌蹇旀綀闁插秴銇婃担?-> 閸忔娊鏁拠?鐟楄儻妫?閺堫亜灏柊宥呭煂
4. 閺傚洦婀伴崥鎴﹀櫤閸栨牠妫舵０?-> "鐟楄儻妫?閸?濮圭喕銈?閸︺劌鎮滈柌蹇曗敄闂傚瓨甯存潻?
鐟欙絽鍠呴弬瑙勵攳閿?1. 濡偓閺屻儲鏆熼幑顔肩氨娑擃厽妲搁崥锔芥箒鐟楄儻妫岄弲顖滃仯
2. 閹绘劙鐝惄闀愭妧鎼达箓妲囬崐?3. 婢х偛濮炵粙鈧悿蹇撴倻闁插繑娼堥柌宥忕礄瑜版挸澧?.2閿涘苯褰查懓鍐0.3-0.5閿?4. 濞ｈ濮為崷鎵倞娴ｅ秶鐤嗘潻鍥ㄦ姢
""")

print("\n" + "=" * 80)
