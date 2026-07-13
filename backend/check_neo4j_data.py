"""Check Neo4j data"""
from app.core.neo4j_client import get_neo4j_client

try:
    client = get_neo4j_client()

    # 1. 检查总数
    result = client.query('MATCH (n:Destination) RETURN count(n) as total')
    total = result[0]['total'] if result else 0
    print(f"\n{'='*60}")
    print(f"Neo4j中的景点总数: {total}")
    print(f"{'='*60}\n")

    if total > 0:
        # 2. 查看示例数据
        sample = client.query('MATCH (n:Destination) RETURN n.name, n.city, n.province LIMIT 5')
        print("示例景点:")
        for i, row in enumerate(sample, 1):
            print(f"  {i}. {row.get('n.name')} - {row.get('n.city')}, {row.get('n.province')}")

        # 3. 检查关系
        relations = client.query("""
            MATCH ()-[r]->()
            RETURN type(r) as rel_type, count(r) as count
        """)
        print(f"\n关系统计:")
        for rel in relations:
            print(f"  - {rel.get('rel_type')}: {rel.get('count')}条")
    else:
        print("⚠️ Neo4j数据库为空！需要先导入景点数据。")

    print(f"\n{'='*60}\n")

except Exception as e:
    print(f"❌ 错误: {e}")
    import traceback
    traceback.print_exc()
