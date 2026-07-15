"""
测试远程MinIO连接和上传
"""
from minio import Minio
import io
import json

# 远程MinIO配置
REMOTE_ENDPOINT = "103.236.98.149:26766"
ACCESS_KEY = "minioadmin"
SECRET_KEY = "minioadmin"
BUCKET_NAME = "travel-documents"
TEST_FILE_NAME = "test-upload.txt"

print("=" * 80)
print("Remote MinIO Connection Test")
print("=" * 80)

# 1. 连接测试
print(f"\n[1/5] Connecting to remote MinIO: {REMOTE_ENDPOINT}")
try:
    client = Minio(
        REMOTE_ENDPOINT,
        access_key=ACCESS_KEY,
        secret_key=SECRET_KEY,
        secure=False
    )
    print("[OK] Connected successfully")
except Exception as e:
    print(f"[ERROR] Connection failed: {e}")
    exit(1)

# 2. 列出所有桶
print(f"\n[2/5] Listing all buckets")
try:
    buckets = client.list_buckets()
    print(f"[OK] Found {len(buckets)} buckets:")
    for bucket in buckets:
        print(f"  - {bucket.name}")
except Exception as e:
    print(f"[ERROR] Failed to list buckets: {e}")

# 3. 检查目标桶是否存在
print(f"\n[3/5] Checking bucket: {BUCKET_NAME}")
try:
    if client.bucket_exists(BUCKET_NAME):
        print(f"[OK] Bucket exists: {BUCKET_NAME}")
    else:
        print(f"[WARNING] Bucket does not exist: {BUCKET_NAME}")
        print(f"[INFO] Creating bucket...")
        client.make_bucket(BUCKET_NAME)
        print(f"[OK] Bucket created: {BUCKET_NAME}")
except Exception as e:
    print(f"[ERROR] Bucket check failed: {e}")

# 4. 测试上传文件
print(f"\n[4/5] Testing file upload")
try:
    test_content = "This is a test file uploaded at 2026-07-15 18:35"
    test_data = io.BytesIO(test_content.encode('utf-8'))

    client.put_object(
        BUCKET_NAME,
        TEST_FILE_NAME,
        test_data,
        length=len(test_content),
        content_type='text/plain'
    )
    print(f"[OK] File uploaded: {TEST_FILE_NAME}")
    print(f"[INFO] URL: http://{REMOTE_ENDPOINT}/{BUCKET_NAME}/{TEST_FILE_NAME}")
except Exception as e:
    print(f"[ERROR] Upload failed: {e}")

# 5. 列出桶中的文件
print(f"\n[5/5] Listing files in bucket: {BUCKET_NAME}")
try:
    objects = client.list_objects(BUCKET_NAME, recursive=True)
    files = list(objects)
    print(f"[OK] Found {len(files)} files:")
    for obj in files:
        print(f"  - {obj.object_name} ({obj.size} bytes)")
except Exception as e:
    print(f"[ERROR] Failed to list files: {e}")

# 6. 设置公共访问策略
print(f"\n[6/6] Setting public access policy")
try:
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
    print(f"[OK] Public policy set successfully")
except Exception as e:
    print(f"[ERROR] Policy setting failed: {e}")

print(f"\n" + "=" * 80)
print("Test completed!")
print("=" * 80)
print(f"\nTest file URL: http://{REMOTE_ENDPOINT}/{BUCKET_NAME}/{TEST_FILE_NAME}")
print(f"Try accessing it in your browser to verify public access.")
