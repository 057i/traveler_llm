"""
Milvus清空脚本

删除所有Milvus collections，重新开始
"""
from pymilvus import connections, utility


def clean_milvus():
    """清空Milvus所有collections"""

    print("=" * 70)
    print("Milvus完全清空脚本")
    print("=" * 70)
    print()

    try:
        # 1. 连接Milvus
        print("[1/4] 连接Milvus...")
        connections.connect(
            alias='default',
            host='localhost',
            port=19530
        )
        print("✓ 连接成功")
        print()

        # 2. 列出所有collections
        print("[2/4] 列出所有collections...")
        collections = utility.list_collections()

        if not collections:
            print("× 没有找到任何collection")
            print()
            print("Milvus已经是空的，无需清空")
            return

        print(f"✓ 找到 {len(collections)} 个collections:")
        for coll in collections:
            print(f"   - {coll}")
        print()

        # 3. 删除所有collections
        print("[3/4] 删除所有collections...")
        for coll in collections:
            print(f"   删除: {coll}")
            utility.drop_collection(coll)
            print(f"   ✓ 已删除: {coll}")
        print()

        # 4. 确认删除
        print("[4/4] 确认删除...")
        remaining = utility.list_collections()

        if len(remaining) == 0:
            print("✓ 所有collections已删除")
            print()
            print("=" * 70)
            print("✓✓✓ Milvus已完全清空！")
            print("=" * 70)
            print()
            print("下一步:")
            print("  1. 重启后端: python main.py")
            print("  2. 后端会自动创建新的collection: travel_destinations")
            print("  3. 上传PDF测试")
        else:
            print(f"❌ 还有 {len(remaining)} 个collections未删除:")
            for coll in remaining:
                print(f"   - {coll}")

    except Exception as e:
        print()
        print(f"❌ 错误: {e}")
        print()
        print("可能的原因:")
        print("  1. Milvus服务未启动")
        print("  2. 连接配置错误 (host/port)")
        print("  3. 权限问题")
        print()
        print("解决方法:")
        print("  1. 检查Milvus是否运行: docker ps | grep milvus")
        print("  2. 检查端口: 19530")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    clean_milvus()
