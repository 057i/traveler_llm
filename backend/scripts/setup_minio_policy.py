"""
设置MinIO桶的公共访问策略
允许公开读取 travel-docs 桶中的文件
"""
from minio import Minio
import json

# MinIO配置
MINIO_ENDPOINT = "127.0.0.1:9000"
MINIO_ACCESS_KEY = "minioadmin"
MINIO_SECRET_KEY = "minioadmin"
BUCKET_NAME = "travel-docs"

# 创建MinIO客户端
client = Minio(
    MINIO_ENDPOINT,
    access_key=MINIO_ACCESS_KEY,
    secret_key=MINIO_SECRET_KEY,
    secure=False
)

# 公共只读策略
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

try:
    # 设置桶策略
    client.set_bucket_policy(BUCKET_NAME, json.dumps(policy))
    print(f"✅ 成功设置 {BUCKET_NAME} 桶为公共只读")
    print(f"现在可以通过以下URL访问文件：")
    print(f"http://{MINIO_ENDPOINT}/{BUCKET_NAME}/文件路径")
except Exception as e:
    print(f"❌ 设置策略失败: {e}")
