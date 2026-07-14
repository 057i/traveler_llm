import redis
from loguru import logger

r = redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)

# 清空所有key
r.flushdb()
logger.success("Flushed Redis DB 0")

# 验证
count = r.dbsize()
logger.info(f"Remaining keys: {count}")

print("Redis cleared successfully")
