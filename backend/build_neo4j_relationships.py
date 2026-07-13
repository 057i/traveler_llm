"""
自动为Neo4j景点建立关系

基于城市/省份建立以下关系：
1. LOCATED_IN - 景点所在城市/省份
2. NEAR_BY - 同城市的景点互为附近
"""
from app.core.neo4j_client import get_neo4j_client
from loguru import logger

def build_neo4j_relationships():
    """为Neo4j景点自动建立关系"""

    client = get_neo4j_client()

    print("\n" + "="*80)
    print("开始建立Neo4j景点关系...")
    print("="*80 + "\n")

    # 1. 建立 LOCATED_IN 关系（景点 -> 城市）
    print("[Step 1] 建立 LOCATED_IN 关系...")
    cypher_located = """
    MATCH (d:Destination)
    WHERE d.city IS NOT NULL AND d.city <> ''
    MERGE (c:City {name: d.city, province: d.province})
    MERGE (d)-[:LOCATED_IN]->(c)
    RETURN count(d) as count
    """

    result = client.query(cypher_located)
    count = result[0]['count'] if result else 0
    print(f"[OK] 创建了 {count} 个 LOCATED_IN 关系\n")

    # 2. 建立 NEAR_BY 关系（同城市的景点互为附近）
    print("[Step 2] 建立 NEAR_BY 关系（同城市景点）...")
    cypher_nearby = """
    MATCH (d1:Destination)-[:LOCATED_IN]->(c:City)<-[:LOCATED_IN]-(d2:Destination)
    WHERE d1.name <> d2.name AND id(d1) < id(d2)
    MERGE (d1)-[:NEAR_BY]-(d2)
    RETURN count(*) as count
    """

    result = client.query(cypher_nearby)
    count = result[0]['count'] if result else 0
    print(f"[OK] 创建了 {count} 个 NEAR_BY 关系\n")

    # 3. 验证结果
    print("[Step 3] 验证关系建立情况...")

    # 统计关系
    cypher_stats = """
    MATCH ()-[r]->()
    RETURN type(r) as rel_type, count(r) as count
    ORDER BY count DESC
    """

    results = client.query(cypher_stats)
    print("\n关系统计:")
    for rel in results:
        print(f"  - {rel['rel_type']}: {rel['count']}条")

    # 4. 测试查询（以"南昌"为例）
    print("\n[Test] 测试查询: 南昌周边景点...")
    cypher_test = """
    MATCH (center:Destination)
    WHERE center.name CONTAINS '南昌' OR center.city CONTAINS '南昌'
    MATCH (center)-[:NEAR_BY|LOCATED_IN*1..2]-(nearby:Destination)
    WHERE nearby.name <> center.name
    RETURN DISTINCT nearby.name as name, nearby.city as city
    LIMIT 5
    """

    results = client.query(cypher_test)
    if results:
        print(f"找到 {len(results)} 个附近景点:")
        for i, r in enumerate(results, 1):
            print(f"  {i}. {r['name']} ({r['city']})")
    else:
        print("[Warning] 未找到附近景点")

    print("\n" + "="*80)
    print("[Success] 关系建立完成！")
    print("="*80 + "\n")

if __name__ == "__main__":
    try:
        build_neo4j_relationships()
    except Exception as e:
        logger.error(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
