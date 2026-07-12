"""
对比优化前后的性能

测试Pipeline优化效果
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
from app.services.document_task import DocumentTaskService

async def test_before_optimization(redis, task_ids):
    """模拟优化前的逐个获取"""
    documents = []
    for task_id in task_ids:
        task_key = f"document:task:{task_id}"
        task_data = redis.get(task_key)
        if task_data:
            documents.append(json.loads(task_data))
    return documents

async def test_comparison():
    """对比测试"""

    redis = get_redis_client()
    service = DocumentTaskService()

    print("=" * 80)
    print("对比优化前后的性能")
    print("=" * 80)
    print()

    tasks_count = redis.llen("document:tasks")
    print(f"文档总数: {tasks_count}")
    print()

    if tasks_count == 0:
        print("× Redis中没有文档数据")
        return

    # 获取task_ids
    test_limit = min(10, tasks_count)
    task_ids = redis.lrange("document:tasks", 0, test_limit - 1)

    print(f"测试数量: {test_limit}个文档")
    print()

    # 测试优化前（逐个获取）
    print("[优化前] 逐个GET...")
    start_time = time.time()
    docs_before = await test_before_optimization(redis, task_ids)
    time_before = time.time() - start_time
    print(f"  耗时: {time_before:.3f}秒")
    print(f"  返回: {len(docs_before)}个文档")
    print()

    # 测试优化后（Pipeline）
    print("[优化后] Pipeline批量获取...")
    start_time = time.time()
    docs_after = await service.list_documents(skip=0, limit=test_limit)
    time_after = time.time() - start_time
    print(f"  耗时: {time_after:.3f}秒")
    print(f"  返回: {len(docs_after)}个文档")
    print()

    # 性能对比
    print("=" * 80)
    print("[性能对比]")
    print("=" * 80)
    print()

    if time_before > 0:
        speedup = time_before / time_after
        improvement = ((time_before - time_after) / time_before) * 100

        print(f"优化前: {time_before:.3f}秒")
        print(f"优化后: {time_after:.3f}秒")
        print(f"性能提升: {speedup:.1f}x")
        print(f"时间节省: {improvement:.1f}%")
        print()

        if speedup > 2:
            print("✓ 优化效果显著！")
        elif speedup > 1.5:
            print("✓ 有明显性能提升")
        else:
            print("○ 性能提升有限（可能是本地Redis，延迟很低）")

    print()
    print("说明:")
    print("  - 本地Redis: 性能提升可能不明显")
    print("  - 远程Redis: 性能提升会更显著")
    print("  - 文档越多: Pipeline优势越大")

if __name__ == "__main__":
    asyncio.run(test_comparison())
