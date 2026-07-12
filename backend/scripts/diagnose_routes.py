"""
鐠囧﹥鏌囬懘姘拱 - 濡偓閺岊檱PI鐠侯垳鏁遍梻顕€顣?"""
import sys
sys.path.insert(0, 'E:/婢堆勀侀崹瀣磻閸?娴狅絿鐖?缂冩垹鐝?travel_proj/backend')

print("=" * 80)
print("鐠囧﹥鏌囧鈧慨?)
print("=" * 80)

print("\n1. 鐎电厧鍙咥PI鐠侯垳鏁卞Ο鈥虫健...")
try:
    from app.api import ai_recommend_new, ai_team_recommend_new
    print(f"OK ai_recommend_new.router.prefix = {ai_recommend_new.router.prefix}")
    print(f"OK ai_team_recommend_new.router.prefix = {ai_team_recommend_new.router.prefix}")

    print(f"\nai_recommend_new 鐠侯垳鏁遍崚妤勩€?")
    for route in ai_recommend_new.router.routes:
        methods = ', '.join(route.methods) if hasattr(route, 'methods') else 'N/A'
        print(f"  - {route.path} [{methods}]")

    print(f"\nai_team_recommend_new 鐠侯垳鏁遍崚妤勩€?")
    for route in ai_team_recommend_new.router.routes:
        methods = ', '.join(route.methods) if hasattr(route, 'methods') else 'N/A'
        print(f"  - {route.path} [{methods}]")

except Exception as e:
    print(f"ERROR 鐎电厧鍙嗘径杈Е: {e}")
    import traceback
    traceback.print_exc()

try:
    from app.services.ai_recommend import get_ai_recommend_service
    service = get_ai_recommend_service()
    print(f"OK AI閹恒劏宕橀張宥呭缁鐎? {type(service).__name__}")
    print(f"OK 閺堝秴濮熷Ο鈥虫健: {type(service).__module__}")
except Exception as e:
    print(f"ERROR 閺堝秴濮熷Λ鈧弻銉ャ亼鐠? {e}")

print("\n3. 濡偓閺岊櫑i_recommend_new.py閻ㄥ嫬顕遍崗?..")
try:
    import inspect
    source = inspect.getsource(ai_recommend_new.ai_recommend_stream_post)
    if 'get_ai_recommend_service' in source:
        print("OK ai_recommend_stream_post 娴ｈ法鏁?get_ai_recommend_service")
    else:
        print("ERROR ai_recommend_stream_post 閺堫亙濞囬悽?get_ai_recommend_service")
        print(f"閸戣姤鏆熷┃鎰垳:\n{source[:500]}")
except Exception as e:
    print(f"ERROR 濡偓閺屻儱銇戠拹? {e}")

print("\n" + "=" * 80)
print("鐠囧﹥鏌囩€瑰本鍨?)
print("=" * 80)
