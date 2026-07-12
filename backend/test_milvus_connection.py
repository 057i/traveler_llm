"""
测试Milvus连接
"""
from pymilvus import connections, utility


def test_connection():
    """测试Milvus连接"""
    print("=" * 70)
    print("测试Milvus连接")
    print("=" * 70)
    print()

    try:
        print("[1/3] 连接Milvus...")
        connections.connect('default', host='localhost', port=19530, timeout=10)
        print("✓ 连接成功")
        print()

        print("[2/3] 列出collections...")
        collections = utility.list_collections()
        print(f"✓ 当前collections: {collections if collections else '(空)'}")
        print()

        print("[3/3] 测试完成")
        print()
        print("=" * 70)
        print("✓✓✓ Milvus运行正常！")
        print("=" * 70)
        print()
        print("下一步:")
        print("  1. python clean_milvus.py (清空旧数据)")
        print("  2. python main.py (启动后端)")
        return True

    except Exception as e:
        print(f"✗ 连接失败: {e}")
        print()
        print("=" * 70)
        print("可能的原因:")
        print("=" * 70)
        print("  1. Milvus未启动")
        print("     → 运行: python diagnose_milvus.py")
        print()
        print("  2. Milvus还在启动中")
        print("     → 等待30秒后重试")
        print()
        print("  3. 端口被占用")
        print("     → netstat -ano | findstr :19530")
        print()
        print("  4. Docker网络问题")
        print("     → docker restart milvus-standalone")
        return False


if __name__ == "__main__":
    test_connection()
    input("\n按Enter退出...")
