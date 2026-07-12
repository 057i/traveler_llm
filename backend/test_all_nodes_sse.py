"""
测试所有节点的SSE事件发送

模拟完整的工作流，检查每个节点是否都发送了开始和结束事件
"""

import asyncio
import sys
import json
sys.path.insert(0, '.')

from app.core.redis_client import get_redis_client

async def test_all_nodes():
    """测试所有节点的事件发送"""

    redis = get_redis_client()
    task_id = "test_full_workflow"

    # 清理之前的测试数据
    event_key = f"document:event:{task_id}"
    events_key = f"document:events:{task_id}"
    redis.delete(event_key)
    redis.delete(events_key)

    print("=" * 80)
    print("测试所有节点的SSE事件发送")
    print("=" * 80)
    print()

    # 导入workflow_service
    from app.workflows.document_processing.workflow_service import DocumentProcessingWorkflow
    workflow_service = DocumentProcessingWorkflow()

    # 模拟所有节点
    nodes = [
        ("minio", "MinIO存储", 10),
        ("parse_pdf_aineru", "PDF解析", 20),
        ("chunk_text", "文本分块", 40),
        ("extract_entities", "实体提取", 60),
        ("vectorize_and_store", "向量化存储", 80),
        ("finalize", "完成处理", 100)
    ]

    for step_id, step_name, progress in nodes:
        print(f"[{step_id}] 发送开始事件...")
        await workflow_service._send_sse_event(task_id, "node_start", {
            "event_type": "node_start",
            "step": step_id,
            "step_name": step_name,
            "status": "processing",
            "message": f"正在{step_name}...",
            "progress": progress
        })

        # 模拟处理延迟
        await asyncio.sleep(0.1)

        print(f"[{step_id}] 发送结束事件...")
        await workflow_service._send_sse_event(task_id, "node_end", {
            "event_type": "node_end",
            "step": step_id,
            "step_name": step_name,
            "status": "completed",
            "message": f"{step_name}完成",
            "progress": progress
        })
        print()

    # 检查Redis中的事件
    print("=" * 80)
    print("检查Redis中的事件")
    print("=" * 80)
    print()

    # 检查最新事件
    event_data = redis.get(event_key)
    if event_data:
        data = json.loads(event_data)
        print(f"✓ 最新事件 (document:event:{task_id}):")
        print(f"  event_type: {data.get('event_type')}")
        print(f"  step: {data.get('step')}")
        print(f"  status: {data.get('status')}")
        print(f"  message: {data.get('message')}")
    else:
        print(f"× 未找到最新事件")
    print()

    # 检查事件列表
    events_count = redis.llen(events_key)
    print(f"✓ 事件列表长度: {events_count}")
    print()

    if events_count > 0:
        print("所有事件详情：")
        print("-" * 80)
        events = redis.lrange(events_key, 0, -1)
        for i, event in enumerate(events, 1):
            data = json.loads(event)
            print(f"{i:2d}. event_type={data.get('event_type'):12s} | "
                  f"step={data.get('step'):20s} | "
                  f"status={data.get('status'):10s} | "
                  f"progress={data.get('progress', 0):3d}%")

    print()
    print("=" * 80)
    print("测试完成")
    print("=" * 80)
    print()

    # 统计结果
    node_start_count = sum(1 for e in events if json.loads(e).get('event_type') == 'node_start')
    node_end_count = sum(1 for e in events if json.loads(e).get('event_type') == 'node_end')

    print(f"统计结果：")
    print(f"  - node_start事件: {node_start_count}")
    print(f"  - node_end事件: {node_end_count}")
    print(f"  - 总事件数: {events_count}")
    print()

    if node_start_count == 6 and node_end_count == 6:
        print("✓ 所有节点都正确发送了开始和结束事件")
    else:
        print("× 事件数量不正确！")
        print(f"  预期: 6个node_start + 6个node_end = 12个事件")
        print(f"  实际: {node_start_count}个node_start + {node_end_count}个node_end = {events_count}个事件")

if __name__ == "__main__":
    asyncio.run(test_all_nodes())
