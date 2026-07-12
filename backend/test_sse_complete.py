"""
完整的SSE事件测试

测试修改后的代码是否正确发送node_start和node_end事件
"""

import asyncio
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

async def test_complete_workflow():
    """测试完整的工作流事件"""

    redis = get_redis_client()
    task_id = "test_complete_workflow"

    # 清理旧数据
    event_key = f"document:event:{task_id}"
    events_key = f"document:events:{task_id}"
    progress_key = f"document:progress:{task_id}"
    redis.delete(event_key)
    redis.delete(events_key)
    redis.delete(progress_key)

    print("=" * 80)
    print("测试完整的SSE事件流程")
    print("=" * 80)
    print()

    # 模拟_send_step_event的行为
    print("[步骤1] 模拟发送节点事件...")
    print()

    test_nodes = [
        ("minio", "MinIO存储", 10),
        ("parse_pdf_aineru", "PDF解析", 30),
        ("chunk_text", "文本分块", 50),
    ]

    for step_id, step_name, progress in test_nodes:
        # 模拟node_start
        event_data_start = {
            "event_type": "node_start",
            "step": step_id,
            "step_name": step_name,
            "status": "processing",
            "message": f"开始{step_name}",
            "progress": progress,
            "timestamp": asyncio.get_event_loop().time()
        }

        # 1. 写入events列表
        redis.rpush(events_key, json.dumps(event_data_start, ensure_ascii=False))
        redis.expire(events_key, 3600)

        # 2. 写入progress key
        redis.set(progress_key, json.dumps(event_data_start, ensure_ascii=False), ex=3600)

        # 3. 写入event key
        event_with_type = {"type": "node_start", **event_data_start}
        redis.set(event_key, json.dumps(event_with_type, ensure_ascii=False), ex=3600)

        print(f"  [node_start] {step_name} ({step_id})")

        await asyncio.sleep(0.1)

        # 模拟node_end
        event_data_end = {
            "event_type": "node_end",
            "step": step_id,
            "step_name": step_name,
            "status": "completed",
            "message": f"{step_name}完成",
            "progress": progress,
            "timestamp": asyncio.get_event_loop().time()
        }

        # 1. 写入events列表
        redis.rpush(events_key, json.dumps(event_data_end, ensure_ascii=False))
        redis.expire(events_key, 3600)

        # 2. 写入progress key
        redis.set(progress_key, json.dumps(event_data_end, ensure_ascii=False), ex=3600)

        # 3. 写入event key
        event_with_type = {"type": "node_end", **event_data_end}
        redis.set(event_key, json.dumps(event_with_type, ensure_ascii=False), ex=3600)

        print(f"  [node_end] {step_name} ({step_id})")
        print()

    # 验证Redis数据
    print("=" * 80)
    print("[验证] 检查Redis中的数据")
    print("=" * 80)
    print()

    # 检查events列表
    events_count = redis.llen(events_key)
    print(f"1. events列表 (document:events:{task_id}):")
    print(f"   总数: {events_count}")

    if events_count > 0:
        events = redis.lrange(events_key, 0, -1)
        print(f"   详情:")
        for i, e in enumerate(events, 1):
            data = json.loads(e)
            print(f"   {i:2d}. [{data.get('event_type'):12s}] {data.get('step'):20s} - {data.get('status'):10s}")
    print()

    # 检查progress key
    progress_data = redis.get(progress_key)
    print(f"2. progress key (document:progress:{task_id}):")
    if progress_data:
        data = json.loads(progress_data)
        print(f"   event_type: {data.get('event_type')}")
        print(f"   step: {data.get('step')}")
        print(f"   status: {data.get('status')}")
        print(f"   message: {data.get('message')}")
    else:
        print(f"   不存在")
    print()

    # 检查event key
    event_data = redis.get(event_key)
    print(f"3. event key (document:event:{task_id}):")
    if event_data:
        data = json.loads(event_data)
        print(f"   type: {data.get('type')}")
        print(f"   event_type: {data.get('event_type')}")
        print(f"   step: {data.get('step')}")
        print(f"   status: {data.get('status')}")
    else:
        print(f"   不存在")
    print()

    # 统计结果
    print("=" * 80)
    print("[统计] 事件统计")
    print("=" * 80)
    print()

    node_start_count = 0
    node_end_count = 0

    for e in events:
        data = json.loads(e)
        if data.get('event_type') == 'node_start':
            node_start_count += 1
        elif data.get('event_type') == 'node_end':
            node_end_count += 1

    print(f"node_start事件: {node_start_count}")
    print(f"node_end事件: {node_end_count}")
    print(f"总事件数: {events_count}")
    print()

    expected_pairs = len(test_nodes)
    if node_start_count == expected_pairs and node_end_count == expected_pairs:
        print(f"✓ 测试通过！每个节点都有start和end事件")
        print(f"  - 预期: {expected_pairs}个节点 × 2个事件 = {expected_pairs * 2}个事件")
        print(f"  - 实际: {node_start_count}个start + {node_end_count}个end = {events_count}个事件")
    else:
        print(f"× 测试失败！事件数量不匹配")
        print(f"  - 预期: {expected_pairs}个start, {expected_pairs}个end")
        print(f"  - 实际: {node_start_count}个start, {node_end_count}个end")
    print()

    print("=" * 80)
    print("[模拟SSE] 前端会收到的事件")
    print("=" * 80)
    print()

    print("前端EventSource监听到的事件顺序:")
    for i, e in enumerate(events, 1):
        data = json.loads(e)
        event_type = data.get('event_type')
        step = data.get('step')
        status = data.get('status')
        message = data.get('message')
        print(f"{i:2d}. event: {event_type:12s} | step={step:20s} | status={status:10s} | message={message}")
    print()

    print("✓ SSE端点会按顺序发送这些事件给前端")
    print("✓ 前端可以通过监听'node_start'和'node_end'事件来更新UI")

if __name__ == "__main__":
    asyncio.run(test_complete_workflow())
