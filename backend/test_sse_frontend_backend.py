"""
完整的前后端SSE测试

模拟上传文档，检查SSE事件流
"""

import asyncio
import sys
import json
import os
import time
from datetime import datetime

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

async def simulate_sse_client(task_id):
    """模拟SSE客户端，检查事件接收"""
    redis = get_redis_client()

    print("=" * 80)
    print(f"模拟SSE客户端连接: {task_id}")
    print("=" * 80)
    print()

    # 1. 读取历史事件（模拟SSE连接时的行为）
    events_key = f"document:events:{task_id}"
    historical_events = redis.lrange(events_key, 0, -1)

    sent_event_ids = set()
    received_events = []

    print(f"[SSE] 发送 {len(historical_events)} 个历史事件...")
    print()

    for i, event_json in enumerate(historical_events, 1):
        event = json.loads(event_json)
        event_type = event.get('event_type')
        step = event.get('step')
        event_id = f"{event_type}:{step}"

        if event_id in sent_event_ids:
            print(f"  × 跳过重复事件: {event_id}")
            continue

        sent_event_ids.add(event_id)
        received_events.append(event)

        print(f"  {i:2d}. [{event_type:12s}] {step:25s}")

    print()
    print("=" * 80)
    print("事件统计")
    print("=" * 80)
    print()

    node_starts = [e for e in received_events if e.get('event_type') == 'node_start']
    node_ends = [e for e in received_events if e.get('event_type') == 'node_end']

    print(f"总事件数: {len(received_events)}")
    print(f"node_start: {len(node_starts)}")
    print(f"node_end: {len(node_ends)}")
    print()

    # 检查每个步骤是否都有start和end
    print("步骤完整性检查:")
    start_steps = set(e.get('step') for e in node_starts)
    end_steps = set(e.get('step') for e in node_ends)

    all_steps = start_steps | end_steps

    for step in sorted(all_steps):
        has_start = step in start_steps
        has_end = step in end_steps

        if has_start and has_end:
            status = "✓"
        else:
            status = "×"

        print(f"  {status} {step:25s} - start:{has_start}  end:{has_end}")

    print()

    # 检查事件顺序
    print("事件顺序检查:")
    last_step = None
    order_correct = True

    for i, event in enumerate(received_events):
        event_type = event.get('event_type')
        step = event.get('step')

        if event_type == 'node_start':
            if last_step is not None and last_step != step:
                print(f"  × 警告: {step} 的 start 出现在 {last_step} 之后，可能顺序错误")
                order_correct = False
            last_step = step
        elif event_type == 'node_end':
            if last_step != step:
                print(f"  × 错误: {step} 的 end 不匹配 start ({last_step})")
                order_correct = False
            last_step = None

    if order_correct:
        print("  ✓ 事件顺序正确")
    print()

    # 总结
    print("=" * 80)
    print("测试结果")
    print("=" * 80)
    print()

    expected_pairs = 7  # minio, parse, chunk, extract, vectorize_traditional, vectorize_graph, finalize

    if len(node_starts) == expected_pairs and len(node_ends) == expected_pairs:
        print("✓ 所有节点事件完整")
    else:
        print(f"× 事件不完整: 预期{expected_pairs}对，实际{len(node_starts)}个start + {len(node_ends)}个end")

    if len(received_events) == len(set(sent_event_ids)):
        print("✓ 无重复事件")
    else:
        print("× 存在重复事件")

    if order_correct:
        print("✓ 事件顺序正确")
    else:
        print("× 事件顺序有问题")

    print()

    return len(received_events), len(node_starts), len(node_ends)

async def main():
    """主测试函数"""
    redis = get_redis_client()

    # 获取最新任务
    task_ids = redis.lrange("document:tasks", 0, 0)

    if not task_ids:
        print("× 没有找到任务，请先上传一个文档")
        print()
        print("测试步骤:")
        print("1. 启动后端: cd backend && python main.py")
        print("2. 打开前端，上传PDF文档")
        print("3. 运行此测试脚本")
        return

    task_id = task_ids[0]

    print(f"测试最新任务: {task_id}")
    print()

    await simulate_sse_client(task_id)

if __name__ == "__main__":
    asyncio.run(main())
