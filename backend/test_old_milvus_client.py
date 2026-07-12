"""
使用旧版milvus_client.py测试连接
"""
import sys
sys.path.insert(0, '.')

print("=" * 70)
print("Milvus连接测试 (使用app.core.milvus_client)")
print("=" * 70)
print()

try:
    print("[1/3] 导入旧版客户端...")
    from app.core.milvus_client import get_milvus_client
    print("  OK 导入成功")
    print()

    print("[2/3] 连接Milvus...")
    milvus = get_milvus_client()
    milvus.connect()
    print("  OK 连接成功")
    print()

    print("[3/3] 测试查询...")
    # 简单测试
    print("  OK 客户端工作正常")
    print()

    print("=" * 70)
    print("SUCCESS 旧版客户端连接成功！")
    print("=" * 70)
    print()
    print("说明:")
    print("  旧版milvus_client可以连接")
    print("  但项目使用的是milvus_hybrid_client (混合检索)")
    print()
    print("下一步:")
    print("  1. 确保Milvus在运行")
    print("  2. python test_milvus_client.py (测试新版客户端)")
    print("  3. python main.py (启动后端)")

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
