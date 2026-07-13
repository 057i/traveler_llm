# -*- coding: utf-8 -*-
import redis
import sys

# 连接Redis
try:
    r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
    r.ping()
    print("Success: Connected to Redis")
except Exception as e:
    print(f"Error: Cannot connect to Redis: {e}")
    sys.exit(1)

print("\n" + "="*80)
print("Cleaning Redis Data")
print("="*80)

# 1. 删除旧session
old_session = "session_1783830930683_766apgr44"
print(f"\n1. Deleting old session: {old_session}")

keys_to_delete = [
    f"ai:recommend:events:{old_session}",
    f"ai_recommend:history:{old_session}",
]

deleted_count = 0
for key in keys_to_delete:
    result = r.delete(key)
    if result > 0:
        print(f"  [OK] Deleted: {key}")
        deleted_count += 1
    else:
        print(f"  [--] Not found: {key}")

# 2. 清理所有AI推荐事件keys
print("\n2. Cleaning all AI recommend event keys")
event_keys = r.keys("ai:recommend:events:*")
if event_keys:
    print(f"  Found {len(event_keys)} event keys")
    for key in event_keys:
        r.delete(key)
        print(f"  [OK] Deleted: {key}")
        deleted_count += 1
else:
    print("  [--] No event keys found")

# 3. 清理所有历史记录keys
print("\n3. Cleaning all history keys")
history_keys = r.keys("ai_recommend:history:*")
if history_keys:
    print(f"  Found {len(history_keys)} history keys")
    for key in history_keys:
        r.delete(key)
        print(f"  [OK] Deleted: {key}")
        deleted_count += 1
else:
    print("  [--] No history keys found")

# 4. 验证清理结果
print("\n4. Verifying cleanup")
remaining_keys = r.keys("ai:recommend:*") + r.keys("ai_recommend:*")
if remaining_keys:
    print(f"  [WARN] Still have {len(remaining_keys)} keys:")
    for key in remaining_keys:
        print(f"    - {key}")
else:
    print("  [OK] All related keys cleaned")

print("\n" + "="*80)
print(f"Redis Cleanup Completed! Deleted {deleted_count} keys")
print("="*80)
print("\nNext steps:")
print("  1. Refresh browser (Ctrl+Shift+R)")
print("  2. Test a query")
print("  3. Check the new session_id")
