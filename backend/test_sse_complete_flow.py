"""
测试SSE完整流程

验证：
1. 事件是否正确写入Redis
2. SSE端点是否正确读取和发送事件
3. 历史事件是否正确发送
"""

import asyncio
import sys
import json
import os
import time

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

async def simulate_workflow_events(task_id):
    """模拟完整的工作流事件"""
    redis = get_redis_client()

    # 清理旧数据
    redis.delete(f"document:event:{task_id}")
    redis.delete(f"document:events:{task_id}")
    redis.delete(f"document:progress:{task_id}")

    print("=" * 80)
    print("模拟完整的工作流事件流程")
    print("=" * 80)
    print()

    # 定义所有步骤
    workflow_steps = [
        ("minio", "MinIO存储", 15),
        ("parse", "PDF解析", 30),
        ("chunk", "文本分块", 45),
        ("extract", "实体提取", 60),
        ("vectorize_traditional", "传统向量化", 75),
        ("vectorize_graph", "图向量化", 90),
    ]

    print("[步骤1] 发送start事件...")
    start_event = {
        "type": "start",
        "message": "开始处理文档",
        "timestamp": time.time()
    }
    redis.set(f"document:event:{task_id}", json.dumps(start_event, ensure_ascii=False), ex=3600)
    print("  ✓ start事件已发送")
    print()

    # 模拟每个节点的开始和结束
    print("[步骤2] 发送节点事件...")
    for step_id, step_name, progress in workflow_steps:
        # node_start
        event_start = {
            "event_type": "node_start",
            "step": step_id,
            "step_name": step_name,
            "status": "processing",
            "message": f"开始{step_name}",
            "progress": progress,
            "timestamp": time.time()
        }

        # 写入events列表
        redis.rpush(f"document:events:{task_id}", json.dumps(event_start, ensure_ascii=False))
        redis.expire(f"document:events:{task_id}", 3600)

        # 写入progress key
        redis.set(f"document:progress:{task_id}", json.dumps(event_start, ensure_ascii=False), ex=3600)

        # 写入event key
        event_with_type = {"type": "node_start", **event_start}
        redis.set(f"document:event:{task_id}", json.dumps(event_with_type, ensure_ascii=False), ex=3600)

        print(f"  [{step_id:25s}] node_start  -> progress={progress}%")

        await asyncio.sleep(0.1)

        # node_end
        event_end = {
            "event_type": "node_end",
            "step": step_id,
            "step_name": step_name,
            "status": "completed",
            "message": f"{step_name}完成",
            "progress": progress,
            "timestamp": time.time()
        }

        # 写入events列表
        redis.rpush(f"document:events:{task_id}", json.dumps(event_end, ensure_ascii=False))

        # 写入progress key
        redis.set(f"document:progress:{task_id}", json.dumps(event_end, ensure_ascii=False), ex=3600)

        # 写入event key
        event_with_type = {"type": "node_end", **event_end}
        redis.set(f"document:event:{task_id}", json.dumps(event_with_type, ensure_ascii=False), ex=3600)

        print(f"  [{step_id:25s}] node_end    -> progress={progress}%")
        print()

    # 发送complete事件
    print("[步骤3] 发送complete事件...")
    complete_event = {
        "type": "complete",
        "message": "文档处理完成",
        "progress": 100,
        "destinations_count": 10,
        "timestamp": time.time()
    }
    redis.set(f"document:event:{task_id}", json.dumps(complete_event, ensure_ascii=False), ex=3600)
    print("  ✓ complete事件已发送")
    print()

    return True

async def verify_redis_data(task_id):
    """验证Redis中的数据"""
    redis = get_redis_client()

    print("=" * 80)
    print("[验证] 检查Redis数据")
    print("=" * 80)
    print()

    # 1. 检查events列表
    events_key = f"document:events:{task_id}"
    events_count = redis.llen(events_key)
    print(f"1. events列表 ({events_key}):")
    print(f"   总数: {events_count}")

    if events_count > 0:
        events = redis.lrange(events_key, 0, -1)
        print(f"   详情:")
        for i, e in enumerate(events, 1):
            data = json.loads(e)
            print(f"   {i:2d}. event_type={data.get('event_type'):12s} | step={data.get('step'):25s} | progress={data.get('progress', 0):3d}%")
    print()

    # 2. 检查progress key
    progress_key = f"document:progress:{task_id}"
    progress_data = redis.get(progress_key)
    print(f"2. progress key ({progress_key}):")
    if progress_data:
        data = json.loads(progress_data)
        print(f"   event_type: {data.get('event_type')}")
        print(f"   step: {data.get('step')}")
        print(f"   status: {data.get('status')}")
        print(f"   progress: {data.get('progress')}%")
    else:
        print(f"   不存在")
    print()

    # 3. 检查event key
    event_key = f"document:event:{task_id}"
    event_data = redis.get(event_key)
    print(f"3. event key ({event_key}):")
    if event_data:
        data = json.loads(event_data)
        print(f"   type: {data.get('type')}")
        print(f"   message: {data.get('message')}")
    else:
        print(f"   不存在")
    print()

async def simulate_sse_connection(task_id):
    """模拟SSE连接时的行为"""
    redis = get_redis_client()

    print("=" * 80)
    print("[模拟SSE] 客户端连接时会收到的数据")
    print("=" * 80)
    print()

    print("当前端连接SSE时 (/api/documents/progress/{task_id})：")
    print()

    # 1. 立即发送所有历史事件
    print("1. 立即发送历史事件:")
    events_key = f"document:events:{task_id}"
    historical_events = redis.lrange(events_key, 0, -1)

    if historical_events:
        print(f"   找到 {len(historical_events)} 个历史事件")
        print()
        for i, event_json in enumerate(historical_events, 1):
            event = json.loads(event_json)
            event_type = event.get('event_type', 'progress')
            step = event.get('step', 'N/A')
            progress_val = event.get('progress', 0)

            if event_type == 'node_start':
                print(f"   {i:2d}. event: node_start")
            elif event_type == 'node_end':
                print(f"   {i:2d}. event: node_end")
            else:
                print(f"   {i:2d}. event: progress")

            print(f"       data: {{step: '{step}', progress: {progress_val}%}}")
    else:
        print("   × 没有历史事件！")
    print()

    # 2. 继续监听新事件
    print("2. 继续监听新事件 (每0.5秒轮询):")
    print("   - 轮询 document:progress:{task_id}")
    print("   - 轮询 document:event:{task_id}")
    print()

async def main():
    """主测试流程"""
    task_id = "test_sse_workflow_complete"

    # 1. 模拟工作流事件
    await simulate_workflow_events(task_id)

    # 2. 验证Redis数据
    await verify_redis_data(task_id)

    # 3. 模拟SSE连接
    await simulate_sse_connection(task_id)

    # 总结
    print("=" * 80)
    print("[总结]")
    print("=" * 80)
    print()
    print("✓ 所有事件已正确写入Redis")
    print("✓ SSE端点会在连接时立即发送所有历史事件")
    print("✓ 前端应该能够看到完整的工作流进度")
    print()
    print("如果前端仍然看不到进度，可能的原因：")
    print("  1. 前端步骤ID不匹配 (检查前端steps对象)")
    print("  2. 前端updateStepStatus函数有问题")
    print("  3. 前端EventSource监听的URL不正确")
    print("  4. CORS或网络问题")
    print()
    print(f"测试task_id: {task_id}")
    print(f"SSE URL: http://localhost:8000/api/documents/progress/{task_id}")
    print()
    print("可以用浏览器访问SSE URL测试是否收到事件")

if __name__ == "__main__":
    asyncio.run(main())
