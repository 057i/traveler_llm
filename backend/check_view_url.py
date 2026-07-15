"""
检查Redis中文档的view_url
"""
from app.services.document_metadata_service import get_document_metadata_service

service = get_document_metadata_service()
docs = service.list_all_documents()

print(f"文档数量: {len(docs)}")
print("=" * 80)

for doc in docs[:5]:  # 只显示前5个
    print(f"\n文档名: {doc.get('filename', '无')}")
    print(f"状态: {doc.get('status', '无')}")
    print(f"view_url: {doc.get('view_url', '无')}")
    print(f"minio_public_url: {doc.get('minio_public_url', '无')}")
    print("-" * 80)
