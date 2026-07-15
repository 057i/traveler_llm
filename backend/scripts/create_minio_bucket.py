"""
手动创建MinIO桶和设置访问策略
"""
from minio import Minio
from minio.commonconfig import ENABLED
import json

# MinIO配置 - 连接到远程MinIO
MINIO_ENDPOINT = "103.236.98.149:27219"  # 远程MinIO地址
MINIO_ACCESS_KEY = "minioadmin"
MINIO_SECRET_KEY = "minioadmin"
BUCKET_NAME = "travel-documents"

print("=" * 80)
print("MinIO Bucket Creation Tool (Remote)")
print("=" * 80)

# 连接MinIO
print(f"\n[1/3] Connecting to MinIO: {MINIO_ENDPOINT}")
try:
    client = Minio(
        MINIO_ENDPOINT,
        access_key=MINIO_ACCESS_KEY,
        secret_key=MINIO_SECRET_KEY,
        secure=False
    )
    print("[OK] MinIO connected successfully")
except Exception as e:
    print(f"[ERROR] MinIO connection failed: {e}")
    exit(1)

# 检查并创建桶
print(f"\n[2/3] Checking bucket: {BUCKET_NAME}")
try:
    if client.bucket_exists(BUCKET_NAME):
        print(f"[OK] Bucket already exists: {BUCKET_NAME}")
    else:
        client.make_bucket(BUCKET_NAME)
        print(f"[OK] Bucket created successfully: {BUCKET_NAME}")
except Exception as e:
    print(f"[ERROR] Bucket operation failed: {e}")
    exit(1)

# 设置公共访问策略
print(f"\n[3/3] Setting public access policy")
try:
    # 策略：允许所有人读取（GetObject）
    policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {"AWS": ["*"]},
                "Action": ["s3:GetObject"],
                "Resource": [f"arn:aws:s3:::{BUCKET_NAME}/*"]
            }
        ]
    }

    client.set_bucket_policy(BUCKET_NAME, json.dumps(policy))
    print(f"[OK] Policy set successfully")
    print(f"\nPolicy content:")
    print(json.dumps(policy, indent=2))

except Exception as e:
    print(f"[ERROR] Policy setting failed: {e}")

# 验证桶列表
print(f"\n" + "=" * 80)
print("Current buckets:")
print("=" * 80)
buckets = client.list_buckets()
for bucket in buckets:
    print(f"  - {bucket.name}")

print(f"\n" + "=" * 80)
print("DONE!")
print("=" * 80)
print(f"\nBucket name: {BUCKET_NAME}")
print(f"Public URL: http://103.236.98.149:26766/{BUCKET_NAME}/")
print(f"Status: Public read-only (anyone can access files)")
print("\nYou can now restart the backend and upload documents for testing.")
