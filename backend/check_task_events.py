"""
检查实际上传任务的Redis数据

用于诊断为什么只有minio发送了node_start
"""

import sys
import json
import os

# 设置控制台编码
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# 设置必要的环境变量
os.environ.setdefault('DASHSCOPE_API_KEY', 'test_key')
os.environ.setdefault('NEO4J_PASSWORD', 'test_password')
os.environ.setdefault('MINERU_API_KEY', 'test_key')

sys.path.insert(0, '.')

from app.core.redis_client import get_redis_client

def check_task_events(task_id):
    """检查指定任务的所有事件"""
    redis = get_redis_client()

    print("=" * 80)
    print(f"检查任务事件: {task_id}")
    print("=" * 80)
    print()

    # 1. 检查events列表
    events_key = f"document:events:{task_id}"
    events_count = redis.llen(events_key)

    print(f"1. events列表 ({events_key}):")
    print(f"   总数: {events_count}")
    print()

    if events_count > 0:
        events = redis.lrange(events_key, 0, -1)
        print("   所有事件:")
        for i, e in enumerate(events, 1):
            data = json.loads(e)
            event_type = data.get('event_type', 'N/A')
            step = data.get('step', 'N/A')
            status = data.get('status', 'N/A')
            message = data.get('message', 'N/A')
            print(f"   {i:2d}. [{event_type:12s}] step={step:25s} status={status:10s}")
            print(f"       message: {message}")
    else:
        print("   × 没有事件记录")
    print()

    # 2. 统计node_start和node_end
    if events_count > 0:
        node_starts = [e for e in events if json.loads(e).get('event_type') == 'node_start']
        node_ends = [e for e in events if json.loads(e).get('event_type') == 'node_end']

        print("2. 事件统计:")
        print(f"   node_start: {len(node_starts)}")
        print(f"   node_end: {len(node_ends)}")
        print()

        if len(node_starts) != len(node_ends):
            print("   ⚠ 警告: node_start和node_end数量不匹配！")
            print()

        # 找出只有end没有start的步骤
        start_steps = set(json.loads(e).get('step') for e in node_starts)
        end_steps = set(json.loads(e).get('step') for e in node_ends)

        missing_starts = end_steps - start_steps
        if missing_starts:
            print(f"   × 缺少node_start的步骤: {missing_starts}")

        missing_ends = start_steps - end_steps
        if missing_ends:
            print(f"   × 缺少node_end的步骤: {missing_ends}")
        print()

    # 3. 检查progress key
    progress_key = f"document:progress:{task_id}"
    progress_data = redis.get(progress_key)

    print(f"3. progress key ({progress_key}):")
    if progress_data:
        data = json.loads(progress_data)
        print(f"   event_type: {data.get('event_type')}")
        print(f"   step: {data.get('step')}")
        print(f"   status: {data.get('status')}")
        print(f"   progress: {data.get('progress')}%")
    else:
        print("   不存在")
    print()

    # 4. 检查event key
    event_key = f"document:event:{task_id}"
    event_data = redis.get(event_key)

    print(f"4. event key ({event_key}):")
    if event_data:
        data = json.loads(event_data)
        print(f"   type: {data.get('type')}")
        if 'message' in data:
            print(f"   message: {data.get('message')}")
    else:
        print("   不存在")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        task_id = sys.argv[1]
    else:
        # 获取最新的任务ID
        redis = get_redis_client()
        task_ids = redis.lrange("document:tasks", 0, 0)
        if task_ids:
            task_id = task_ids[0]
            print(f"使用最新任务ID: {task_id}")
            print()
        else:
            print("错误: 没有找到任务")
            print("用法: python check_task_events.py [task_id]")
            sys.exit(1)

    check_task_events(task_id)
