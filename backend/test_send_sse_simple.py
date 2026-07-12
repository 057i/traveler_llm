"""
直接测试_send_sse_event方法
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

async def test_send_sse_event():
    """直接测试SSE事件发送"""

    redis = get_redis_client()
    task_id = "test_direct_sse"

    # 清理旧数据
    event_key = f"document:event:{task_id}"
    events_key = f"document:events:{task_id}"
    redis.delete(event_key)
    redis.delete(events_key)

    print("=" * 80)
    print("直接测试 _send_sse_event 方法")
    print("=" * 80)
    print()

    # 方法1: 直接写入Redis（绕过workflow_service）
    print("[测试1] 直接写入Redis...")

    # 写入event key
    event_data = {
        "event_type": "node_start",
        "step": "test_step",
        "step_name": "测试步骤",
        "status": "processing",
        "message": "测试消息",
        "progress": 50
    }
    redis.set(event_key, json.dumps(event_data), ex=300)
    print(f"  ✓ 写入 {event_key}")

    # 写入events列表
    redis.rpush(events_key, json.dumps(event_data))
    redis.expire(events_key, 300)
    print(f"  ✓ 写入 {events_key}")
    print()

    # 验证写入
    print("[验证1] 检查Redis数据...")
    stored_event = redis.get(event_key)
    if stored_event:
        data = json.loads(stored_event)
        print(f"  ✓ event key存在")
        print(f"    event_type: {data.get('event_type')}")
        print(f"    step: {data.get('step')}")
        print(f"    message: {data.get('message')}")
    else:
        print(f"  × event key不存在")
    print()

    events_count = redis.llen(events_key)
    print(f"  ✓ events列表长度: {events_count}")
    if events_count > 0:
        events = redis.lrange(events_key, 0, -1)
        for i, e in enumerate(events, 1):
            data = json.loads(e)
            print(f"    事件{i}: {data.get('event_type')} - {data.get('step')}")
    print()

    # 清理
    redis.delete(event_key)
    redis.delete(events_key)

    # 方法2: 使用workflow_service的_send_sse_event方法
    print("=" * 80)
    print("[测试2] 使用 workflow_service._send_sse_event 方法...")
    print("=" * 80)
    print()

    from app.workflows.document_processing.workflow_service import DocumentProcessingWorkflow
    workflow = DocumentProcessingWorkflow()

    # 发送node_start事件
    print("发送 node_start 事件...")
    await workflow._send_sse_event(task_id, "node_start", {
        "event_type": "node_start",
        "step": "minio",
        "step_name": "MinIO存储",
        "status": "processing",
        "message": "开始MinIO存储",
        "progress": 10
    })
    print("  ✓ node_start 已发送")
    print()

    # 发送node_end事件
    print("发送 node_end 事件...")
    await workflow._send_sse_event(task_id, "node_end", {
        "event_type": "node_end",
        "step": "minio",
        "step_name": "MinIO存储",
        "status": "completed",
        "message": "MinIO存储完成",
        "progress": 10
    })
    print("  ✓ node_end 已发送")
    print()

    # 验证
    print("[验证2] 检查通过workflow_service发送的事件...")
    stored_event = redis.get(event_key)
    if stored_event:
        data = json.loads(stored_event)
        print(f"  ✓ event key存在")
        print(f"    event_type: {data.get('event_type')}")
        print(f"    step: {data.get('step')}")
        print(f"    status: {data.get('status')}")
        print(f"    message: {data.get('message')}")
    else:
        print(f"  × event key不存在！_send_sse_event可能没有正确写入Redis")
    print()

    events_count = redis.llen(events_key)
    print(f"  events列表长度: {events_count}")
    if events_count > 0:
        events = redis.lrange(events_key, 0, -1)
        print(f"  ✓ events列表有数据:")
        for i, e in enumerate(events, 1):
            data = json.loads(e)
            print(f"    {i}. event_type={data.get('event_type')}, step={data.get('step')}, status={data.get('status')}")
    else:
        print(f"  × events列表为空！_send_sse_event可能没有正确写入")
    print()

    print("=" * 80)
    print("结论：")
    print("=" * 80)
    if stored_event and events_count > 0:
        print("✓ _send_sse_event工作正常")
        print("✓ Redis写入正常")
        print("问题可能在前端SSE监听或网络传输")
    else:
        print("× _send_sse_event有问题！")
        print("× 需要检查workflow_service.py中的_send_sse_event实现")

if __name__ == "__main__":
    asyncio.run(test_send_sse_event())
