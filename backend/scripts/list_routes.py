"""
閸掓鍤璅astAPI鎼存梻鏁ら惃鍕閺堝鐭鹃悽?"""
import sys
sys.path.insert(0, 'E:/婢堆勀侀崹瀣磻閸?娴狅絿鐖?缂冩垹鐝?travel_proj/backend')

from main import app

print("=" * 80)
print("FastAPI鎼存梻鏁ら惃鍕閺堝鐭鹃悽?)
print("=" * 80)

print("\n閺屻儲澹橀幍鈧張澶婂瘶閸?recommend'閹?stream'閻ㄥ嫯鐭鹃悽?")
print("-" * 80)

for route in app.routes:
    path = getattr(route, 'path', '')
    methods = getattr(route, 'methods', set())
    name = getattr(route, 'name', '')

    if 'recommend' in path or 'stream' in path:
        print(f"\n鐠侯垰绶? {path}")
        print(f"  閺傝纭? {', '.join(methods) if methods else 'N/A'}")
        print(f"  閸氬秶袨: {name}")

        # 婵″倹鐏夐張濉璶dpoint閿涘本妯夌粈鍝勭暊
        if hasattr(route, 'endpoint'):
            endpoint = route.endpoint
            print(f"  閸戣姤鏆? {endpoint.__module__}.{endpoint.__name__}")

print("\n" + "=" * 80)
print("鐎瑰本鍨?)
print("=" * 80)
