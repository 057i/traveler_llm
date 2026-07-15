"""
设置MinIO travel-documents桶的公共访问策略
"""
from minio import Minio
import json

ENDPOINT = "103.236.98.149:26766"
ACCESS_KEY = "minioadmin"
SECRET_KEY = "minioadmin"
BUCKET_NAME = "travel-documents"

print("=" * 80)
print("Setting MinIO Public Access Policy")
print("=" * 80)

# 1. 连接MinIO
print(f"\n[1/2] Connecting to: {ENDPOINT}")
client = Minio(ENDPOINT, access_key=ACCESS_KEY, secret_key=SECRET_KEY, secure=False)
print("[OK] Connected")

# 2. 设置公共访问策略
print(f"\n[2/2] Setting public read policy for bucket: {BUCKET_NAME}")
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
    print("[OK] Public policy set successfully")
    print("\nPolicy content:")
    print(json.dumps(policy, indent=2))

except Exception as e:
    print(f"[ERROR] Failed to set policy: {e}")
    exit(1)

print("\n" + "=" * 80)
print("DONE!")
print("=" * 80)
print(f"\nAll files in {BUCKET_NAME} are now publicly accessible.")
print(f"Test URL: http://{ENDPOINT}/{BUCKET_NAME}/test-upload.txt")
