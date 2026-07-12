"""
使用现有的milvus_hybrid_client测试连接
"""
import sys
sys.path.insert(0, '.')

print("=" * 70)
print("Milvus连接测试 (使用milvus_hybrid_client)")
print("=" * 70)
print()

try:
    print("[1/3] 导入客户端...")
    from app.core.milvus_hybrid_client import get_milvus_hybrid_client
    print("  OK 导入成功")
    print()

    print("[2/3] 连接Milvus...")
    milvus = get_milvus_hybrid_client()
    print("  OK 连接成功")
    print()

    print("[3/3] 获取数据统计...")
    count = milvus.get_count()
    print(f"  OK 当前向量数: {count}")
    print()

    print("=" * 70)
    print("SUCCESS 所有测试通过！")
    print("=" * 70)
    print()
    print("Milvus运行正常，可以启动后端了")
    print()
    print("下一步:")
    print("  1. python clean_milvus.py (清空旧数据)")
    print("  2. python main.py (启动后端)")

except Exception as e:
    print(f"  ERROR 失败: {e}")
    print()
    print("=" * 70)
    print("连接失败，请检查:")
    print("=" * 70)
    print()
    print("1. Milvus是否运行?")
    print("   docker ps | findstr milvus")
    print()
    print("2. 如果没有运行，启动它:")
    print("   docker start milvus-standalone")
    print()
    print("   或创建新容器:")
    print("   docker run -d --name milvus-standalone -p 19530:19530 milvusdb/milvus:latest")
    print()
    print("3. 等待30秒后重试")
    print()
    import traceback
    traceback.print_exc()

input("\n按Enter退出...")
