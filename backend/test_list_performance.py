"""
测试/api/documents/list接口性能

分析性能瓶颈
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

async def test_list_performance():
    """测试list接口性能"""

    redis = get_redis_client()
    service = DocumentTaskService()

    print("=" * 80)
    print("测试 /api/documents/list 接口性能")
    print("=" * 80)
    print()

    # 1. 检查Redis中有多少文档
    print("[步骤1] 检查Redis数据...")
    tasks_count = redis.llen("document:tasks")
    print(f"  文档总数: {tasks_count}")
    print()

    if tasks_count == 0:
        print("× Redis中没有文档数据，无法测试")
        return

    # 2. 测试list_documents性能
    print("[步骤2] 测试 list_documents 方法...")

    start_time = time.time()
    documents = await service.list_documents(skip=0, limit=10)
    elapsed = time.time() - start_time

    print(f"  返回文档数: {len(documents)}")
    print(f"  耗时: {elapsed:.3f}秒")

    if elapsed > 1.0:
        print(f"  ⚠ 性能警告: 耗时超过1秒")
    print()

    # 3. 测试count_documents性能
    print("[步骤3] 测试 count_documents 方法...")

    start_time = time.time()
    total = await service.count_documents()
    elapsed = time.time() - start_time

    print(f"  总数: {total}")
    print(f"  耗时: {elapsed:.3f}秒")
    print()

    # 4. 分析每个文档的数据大小
    print("[步骤4] 分析文档数据...")

    if documents:
        first_doc = documents[0]
        doc_json = json.dumps(first_doc, ensure_ascii=False)
        doc_size = len(doc_json.encode('utf-8'))

        print(f"  单个文档数据大小: {doc_size} bytes")
        print(f"  文档字段数: {len(first_doc)}")
        print(f"  文档字段: {', '.join(first_doc.keys())}")
        print()

    # 5. 测试逐个获取的性能
    print("[步骤5] 测试逐个获取文档的性能...")

    task_ids = redis.lrange("document:tasks", 0, 9)
    print(f"  获取前10个task_id耗时: ", end="")

    start_time = time.time()
    task_ids = redis.lrange("document:tasks", 0, 9)
    elapsed = time.time() - start_time
    print(f"{elapsed:.3f}秒")

    print(f"  逐个获取文档数据:")
    total_get_time = 0

    for i, task_id in enumerate(task_ids[:3], 1):  # 只测试前3个
        task_key = f"document:task:{task_id}"

        start_time = time.time()
        task_data = redis.get(task_key)
        elapsed = time.time() - start_time
        total_get_time += elapsed

        if task_data:
            data = json.loads(task_data)
            print(f"    {i}. {task_key}: {elapsed:.3f}秒 (size: {len(task_data)} bytes)")
        else:
            print(f"    {i}. {task_key}: 不存在")

    avg_get_time = total_get_time / 3
    estimated_10_docs = avg_get_time * 10

    print(f"  平均单个get耗时: {avg_get_time:.3f}秒")
    print(f"  估计10个文档总耗时: {estimated_10_docs:.3f}秒")
    print()

    # 6. 性能分析
    print("=" * 80)
    print("[性能分析]")
    print("=" * 80)
    print()

    print("可能的性能瓶颈:")
    print()

    if tasks_count > 100:
        print("1. ⚠ 文档数量较多")
        print(f"   - 当前: {tasks_count}个文档")
        print(f"   - 建议: 考虑添加索引或缓存")
        print()

    if avg_get_time > 0.1:
        print("2. ⚠ Redis GET操作较慢")
        print(f"   - 平均耗时: {avg_get_time:.3f}秒")
        print(f"   - 可能原因: Redis网络延迟或数据量大")
        print()

    if documents and len(doc_json) > 10000:
        print("3. ⚠ 单个文档数据较大")
        print(f"   - 大小: {doc_size} bytes")
        print(f"   - 建议: 考虑只返回必要字段")
        print()

    # 7. 优化建议
    print("=" * 80)
    print("[优化建议]")
    print("=" * 80)
    print()

    print("1. 使用Redis Pipeline批量获取文档")
    print("   - 当前: 逐个GET，N次往返")
    print("   - 优化: 使用pipeline一次性获取，1次往返")
    print()

    print("2. 只返回列表必需的字段")
    print("   - 当前: 返回所有字段")
    print("   - 优化: 只返回id, filename, status等关键字段")
    print()

    print("3. 添加Redis缓存")
    print("   - 缓存列表数据，设置较短的TTL（如30秒）")
    print()

    # 8. 测试Pipeline优化
    print("=" * 80)
    print("[测试Pipeline优化]")
    print("=" * 80)
    print()

    print("使用Pipeline批量获取10个文档...")
    task_ids = redis.lrange("document:tasks", 0, 9)

    start_time = time.time()

    # 使用pipeline
    if redis.client:
        pipeline = redis.client.pipeline()
        for task_id in task_ids:
            task_key = f"document:task:{task_id}"
            pipeline.get(task_key)
        results = pipeline.execute()

        elapsed = time.time() - start_time

        print(f"  Pipeline耗时: {elapsed:.3f}秒")
        print(f"  对比逐个获取: {estimated_10_docs:.3f}秒")

        if estimated_10_docs > 0:
            speedup = estimated_10_docs / elapsed
            print(f"  性能提升: {speedup:.1f}x")
        print()

        if elapsed < 0.1:
            print("✓ Pipeline优化后性能良好！")
        else:
            print("⚠ 即使使用Pipeline，性能仍需改进")

if __name__ == "__main__":
    asyncio.run(test_list_performance())
