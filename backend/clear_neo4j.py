from neo4j import GraphDatabase
from loguru import logger

driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "..123456"))

with driver.session() as session:
    # 删除所有节点和关系
    result = session.run("MATCH (n) DETACH DELETE n")
    logger.success("Deleted all nodes and relationships")
    
    # 验证
    count = session.run("MATCH (n) RETURN count(n) as count").single()["count"]
    logger.info(f"Remaining nodes: {count}")

driver.close()
print("Neo4j cleared successfully")
