"""
完整的端到端SSE测试

1. 模拟文档上传
2. 实时监听SSE事件
3. 验证事件完整性和实时性
"""

import asyncio
import aiohttp
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

class SSEEventCollector:
    def __init__(self):
        self.events = []
        self.start_time = None
        self.event_times = {}

    def add_event(self, event_type, data, timestamp):
        self.events.append({
            'type': event_type,
            'data': data,
            'timestamp': timestamp,
            'elapsed': (timestamp - self.start_time) * 1000 if self.start_time else 0
        })

        # 记录每个步骤的时间
        step = data.get('step')
        if step:
            event_id = f"{event_type}:{step}"
            self.event_times[event_id] = timestamp

    def analyze(self):
        print("=" * 80)
        print("SSE事件分析")
        print("=" * 80)
        print()

        # 统计
        node_starts = [e for e in self.events if e['type'] == 'node_start']
        node_ends = [e for e in self.events if e['type'] == 'node_end']

        print(f"总事件数: {len(self.events)}")
        print(f"node_start: {len(node_starts)}")
        print(f"node_end: {len(node_ends)}")
        print()

        # 检查重复
        event_ids = []
        for e in self.events:
            if e['type'] in ['node_start', 'node_end']:
                step = e['data'].get('step')
                event_id = f"{e['type']}:{step}"
                event_ids.append(event_id)

        duplicates = len(event_ids) - len(set(event_ids))
        if duplicates > 0:
            print(f"× 发现 {duplicates} 个重复事件")
        else:
            print("✓ 无重复事件")
        print()

        # 时间线
        print("事件时间线:")
        for i, e in enumerate(self.events, 1):
            event_type = e['type']
            step = e['data'].get('step', '-')
            elapsed = e['elapsed']
            print(f"  {i:2d}. [{elapsed:7.0f}ms] {event_type:12s} {step}")
        print()

        # 延迟分析
        print("延迟分析:")
        if len(self.events) > 1:
            delays = []
            for i in range(1, len(self.events)):
                delay = (self.events[i]['timestamp'] - self.events[i-1]['timestamp']) * 1000
                delays.append(delay)

            avg_delay = sum(delays) / len(delays)
            max_delay = max(delays)

            print(f"  平均延迟: {avg_delay:.1f}ms")
            print(f"  最大延迟: {max_delay:.1f}ms")

            if avg_delay < 200:
                print("  ✓ 延迟良好")
            else:
                print(f"  × 延迟过高")
        print()

        # 完整性检查
        print("完整性检查:")
        start_steps = set(e['data'].get('step') for e in node_starts)
        end_steps = set(e['data'].get('step') for e in node_ends)

        all_steps = start_steps | end_steps
        complete = True

        for step in sorted(all_steps):
            has_start = step in start_steps
            has_end = step in end_steps

            if has_start and has_end:
                status = "✓"
            else:
                status = "×"
                complete = False

            print(f"  {status} {step:25s} - start:{has_start}  end:{has_end}")

        print()

        return {
            'total': len(self.events),
            'starts': len(node_starts),
            'ends': len(node_ends),
            'duplicates': duplicates,
            'complete': complete,
            'avg_delay': avg_delay if len(self.events) > 1 else 0
        }

async def test_sse_realtime():
    """测试SSE实时事件"""

    print("=" * 80)
    print("SSE实时事件测试")
    print("=" * 80)
    print()

    # 获取最新任务
    redis = get_redis_client()
    task_ids = redis.lrange("document:tasks", 0, 0)

    if not task_ids:
        print("× 没有找到任务")
        print()
        print("请先：")
        print("1. 启动后端服务")
        print("2. 上传一个PDF文档")
        print("3. 重新运行此测试")
        return False

    task_id = task_ids[0]
    print(f"测试任务: {task_id}")
    print()

    # 创建事件收集器
    collector = SSEEventCollector()
    collector.start_time = time.time()

    # 连接SSE
    url = f"http://localhost:8000/api/documents/progress/{task_id}"
    print(f"连接SSE: {url}")
    print()

    try:
        timeout = aiohttp.ClientTimeout(total=60)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url) as response:
                print("✓ SSE连接成功")
                print()
                print("接收事件中...")
                print("-" * 80)

                async for line in response.content:
                    line = line.decode('utf-8').strip()

                    if line.startswith('event:'):
                        event_type = line.split(':', 1)[1].strip()
                    elif line.startswith('data:'):
                        data_str = line.split(':', 1)[1].strip()
                        try:
                            data = json.loads(data_str)
                            timestamp = time.time()

                            collector.add_event(event_type, data, timestamp)

                            # 实时显示
                            step = data.get('step', '-')
                            elapsed = (timestamp - collector.start_time) * 1000
                            print(f"[{elapsed:7.0f}ms] {event_type:12s} {step}")

                            # 如果收到complete事件，结束
                            if event_type == 'complete':
                                print("-" * 80)
                                print("✓ 收到complete事件，测试完成")
                                print()
                                break

                        except json.JSONDecodeError:
                            pass

    except asyncio.TimeoutError:
        print()
        print("× 连接超时")
        return False
    except Exception as e:
        print()
        print(f"× 错误: {e}")
        import traceback
        traceback.print_exc()
        return False

    # 分析结果
    result = collector.analyze()

    # 总结
    print("=" * 80)
    print("测试总结")
    print("=" * 80)
    print()

    all_passed = True

    if result['total'] >= 14:
        print(f"✓ 事件数量: {result['total']} (预期>=14)")
    else:
        print(f"× 事件数量不足: {result['total']} (预期>=14)")
        all_passed = False

    if result['duplicates'] == 0:
        print("✓ 无重复事件")
    else:
        print(f"× 有{result['duplicates']}个重复事件")
        all_passed = False

    if result['complete']:
        print("✓ 所有节点事件完整")
    else:
        print("× 部分节点事件缺失")
        all_passed = False

    if result['avg_delay'] < 200:
        print(f"✓ 平均延迟: {result['avg_delay']:.1f}ms (良好)")
    else:
        print(f"× 平均延迟: {result['avg_delay']:.1f}ms (过高)")
        all_passed = False

    print()

    if all_passed:
        print("🎉 所有测试通过！SSE实时事件工作正常")
    else:
        print("❌ 部分测试失败，需要修复")

    return all_passed

if __name__ == "__main__":
    try:
        result = asyncio.run(test_sse_realtime())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print()
        print("测试被中断")
        sys.exit(1)
