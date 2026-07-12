"""
直接读取progress key的原始JSON
"""

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

if __name__ == "__main__":
    redis = get_redis_client()

    if len(sys.argv) > 1:
        task_id = sys.argv[1]
    else:
        task_ids = redis.lrange("document:tasks", 0, 0)
        if task_ids:
            task_id = task_ids[0]
        else:
            print("没有找到任务")
            sys.exit(1)

    print(f"Task ID: {task_id}")
    print()

    # 读取progress key
    progress_key = f"document:progress:{task_id}"
    progress_data = redis.get(progress_key)

    print(f"progress key: {progress_key}")
    print()

    if progress_data:
        print("原始JSON:")
        print(progress_data)
        print()
        print("解析后:")
        data = json.loads(progress_data)
        for key, value in data.items():
            print(f"  {key}: {value}")
    else:
        print("不存在")
