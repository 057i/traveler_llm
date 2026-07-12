"""
快速测试Redis Pub/Sub实时推送

验证SSE事件延迟
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

os.environ.setdefault('DASHSCOPE_API_KEY', 'test_key')
os.environ.setdefault('NEO4J_PASSWORD', 'test_password')
os.environ.setdefault('MINERU_API_KEY', 'test_key')

sys.path.insert(0, '.')

from app.core.redis_client import get_redis_client

async def test_pubsub():
    """测试Redis Pub/Sub"""
    redis = get_redis_client()

    print("=" * 80)
    print("Redis Pub/Sub 测试")
    print("=" * 80)
    print()

    task_id = "test_pubsub_123"
    channel = f"document:events:{task_id}"

    print(f"频道: {channel}")
    print()

    # 创建订阅者
    import redis as redis_lib
    from config.settings import settings

    pubsub_client = redis_lib.Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        db=settings.REDIS_DB,
        password=settings.REDIS_PASSWORD if settings.REDIS_PASSWORD else None,
        decode_responses=True
    )

    pubsub = pubsub_client.pubsub()
    pubsub.subscribe(channel)

    print("✓ 订阅者已准备")
    print()

    # 发布消息
    print("发布测试消息...")
    messages = [
        {"type": "node_start", "step": "test1", "message": "测试1开始"},
        {"type": "node_end", "step": "test1", "message": "测试1完成"},
        {"type": "node_start", "step": "test2", "message": "测试2开始"},
        {"type": "node_end", "step": "test2", "message": "测试2完成"},
    ]

    publish_times = {}

    for i, msg in enumerate(messages, 1):
        send_time = time.time()
        redis.client.publish(channel, json.dumps(msg, ensure_ascii=False))
        publish_times[msg['step'] + '_' + msg['type']] = send_time
        print(f"  {i}. 发布: {msg['type']} - {msg['step']}")
        await asyncio.sleep(0.1)

    print()
    print("接收消息...")

    received = 0
    max_wait = 50  # 5秒

    for _ in range(max_wait):
        message = pubsub.get_message(timeout=0.1)

        if message and message['type'] == 'message':
            receive_time = time.time()
            data = json.loads(message['data'])

            msg_type = data['type']
            step = data['step']
            key = step + '_' + msg_type

            if key in publish_times:
                latency = (receive_time - publish_times[key]) * 1000
                print(f"  ✓ 收到: {msg_type} - {step} (延迟: {latency:.2f}ms)")
                received += 1

                if received == len(messages):
                    break

        await asyncio.sleep(0.1)

    pubsub.unsubscribe()
    pubsub.close()
    pubsub_client.close()

    print()
    print("=" * 80)
    print("测试结果")
    print("=" * 80)
    print()

    if received == len(messages):
        print(f"✓ 所有消息接收成功 ({received}/{len(messages)})")
        print("✓ Redis Pub/Sub 工作正常")
        return True
    else:
        print(f"× 部分消息丢失 ({received}/{len(messages)})")
        print("× Redis Pub/Sub 可能有问题")
        return False

if __name__ == "__main__":
    try:
        result = asyncio.run(test_pubsub())
        sys.exit(0 if result else 1)
    except Exception as e:
        print(f"× 错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
