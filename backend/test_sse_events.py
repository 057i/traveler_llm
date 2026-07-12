"""
SSE事件测试脚本

用于验证workflow_service是否正确发送所有SSE事件
"""

import asyncio
import sys
sys.path.insert(0, '.')

from app.workflows.document_processing.workflow_service import DocumentProcessingWorkflow

async def test_sse_events():
    """测试SSE事件发送"""

    # 创建workflow实例
    workflow_service = DocumentProcessingWorkflow()

    # 模拟task_id
    task_id = "test_task_123"

    print("=" * 80)
    print("开始测试SSE事件发送")
    print("=" * 80)
    print()

    # 测试发送node_start事件
    print("[测试1] 发送node_start事件...")
    await workflow_service._send_step_event(
        task_id=task_id,
        step_id="minio",
        step_name="MinIO存储",
        status="processing",
        message="正在保存文件到MinIO...",
        progress=15,
        event_type="node_start"
    )
    print("  ✓ node_start事件已发送")
    print()

    # 测试发送node_end事件
    print("[测试2] 发送node_end事件...")
    await workflow_service._send_step_event(
        task_id=task_id,
        step_id="minio",
        step_name="MinIO存储",
        status="completed",
        message="文件保存成功",
        progress=15,
        event_type="node_end"
    )
    print("  ✓ node_end事件已发送")
    print()

    # 检查Redis中的事件
    print("[测试3] 检查Redis中的事件...")
    from app.core.redis_client import get_redis_client
    redis = get_redis_client()

    # 检查event key
    event_key = f"document:event:{task_id}"
    event_data = redis.get(event_key)
    if event_data:
        import json
        data = json.loads(event_data)
        print(f"  ✓ Redis event key存在: {event_key}")
        print(f"  内容: {json.dumps(data, ensure_ascii=False, indent=2)}")
    else:
        print(f"  × Redis event key不存在: {event_key}")
    print()

    # 检查events列表
    events_key = f"document:events:{task_id}"
    events_count = redis.llen(events_key)
    print(f"  ✓ Redis events列表长度: {events_count}")

    if events_count > 0:
        # 获取所有事件
        events = redis.lrange(events_key, 0, -1)
        for i, event in enumerate(events, 1):
            import json
            data = json.loads(event)
            print(f"  事件{i}: event_type={data.get('event_type')}, step={data.get('step')}, status={data.get('status')}")
    print()

    print("=" * 80)
    print("测试完成")
    print("=" * 80)
    print()
    print("结论：")
    print("  1. 如果Redis中有数据，说明_send_step_event工作正常")
    print("  2. 如果前端没收到，说明_send_sse_event有问题")
    print("  3. 需要检查_send_sse_event是否正确写入Redis event key")
    print()

if __name__ == "__main__":
    asyncio.run(test_sse_events())
