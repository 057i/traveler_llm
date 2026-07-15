"""
检查MinIO中的文件列表
"""
from minio import Minio

# 远程MinIO配置
ENDPOINT = "103.236.98.149:26766"
ACCESS_KEY = "minioadmin"
SECRET_KEY = "minioadmin"
BUCKET_NAME = "travel-documents"

print("=" * 80)
print("Checking MinIO Files")
print("=" * 80)

# 连接MinIO
print(f"\n[1/2] Connecting to: {ENDPOINT}")
client = Minio(ENDPOINT, access_key=ACCESS_KEY, secret_key=SECRET_KEY, secure=False)
print("[OK] Connected")

# 列出所有文件
print(f"\n[2/2] Listing all files in bucket: {BUCKET_NAME}")
try:
    objects = client.list_objects(BUCKET_NAME, recursive=True)
    files = list(objects)

    print(f"[OK] Found {len(files)} files:\n")

    for obj in files:
        print(f"  File: {obj.object_name}")
        print(f"     Size: {obj.size} bytes")
        print(f"     Last Modified: {obj.last_modified}")
        print(f"     URL: http://{ENDPOINT}/{BUCKET_NAME}/{obj.object_name}")
        print()

    if len(files) == 0:
        print("  WARNING: Bucket is empty!")

except Exception as e:
    print(f"[ERROR] Failed: {e}")

print("=" * 80)
