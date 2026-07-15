"""
Neo4j Client - Graph Database
"""
from neo4j import GraphDatabase
from loguru import logger
from typing import Dict, Any, List, Optional
import os


class Neo4jClient:
    """
    Neo4j客户端 - 图数据库服务

    功能：
    - 创建节点（景点、城市等）
    - 创建关系（位于、附近等）
    - Cypher查询执行
    - 图谱查询（附近景点推荐）

    使用场景：
    - 存储景点地理关系
    - 查询附近景点
    - 构建知识图谱
    - 基于关系的推荐
    """

    def __init__(self, uri: str = None, user: str = None, password: str = None):
        """
        Initialize Neo4j client

        Args:
            uri: Neo4j connection URI
            user: Neo4j username
            password: Neo4j password
        """
        from config.settings import settings

        self.uri = uri if uri is not None else settings.NEO4J_URI
        self.user = user if user is not None else settings.NEO4J_USER
        self.password = password if password is not None else settings.NEO4J_PASSWORD

        logger.info(f"[Neo4j] Connecting to {self.uri} as {self.user}")

        # Initialize driver
        self.driver = GraphDatabase.driver(
            self.uri,
            auth=(self.user, self.password),
            max_connection_lifetime=3600
        )

        # Test connection with retry
        max_retries = 3
        for attempt in range(max_retries):
            try:
                self.driver.verify_connectivity()
                logger.success(f"[Neo4j] Connected to {self.uri}")
                break
            except Exception as e:
                if attempt < max_retries - 1:
                    logger.warning(f"[Neo4j] Connection attempt {attempt + 1} failed, retrying...")
                    import time
                    time.sleep(1)
                else:
                    logger.error(f"[Neo4j] Connection failed after {max_retries} attempts: {e}")

    def close(self):
        """Close Neo4j driver"""
        if self.driver:
            self.driver.close()

    def query(self, cypher: str, parameters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Execute a Cypher query and return results

        Args:
            cypher: Cypher query string
            parameters: Query parameters

        Returns:
            List of result records as dictionaries
        """
        if parameters is None:
            parameters = {}

        with self.driver.session() as session:
            result = session.run(cypher, parameters)
            records = [record.data() for record in result]
            return records

    def create_destination(
        self,
        name: str,
        description: str = "",
        location: str = "",
        properties: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Create a Destination node (wrapper for create_destination_node)

        Args:
            name: Destination name
            description: Description
            location: Location string
            properties: Additional properties

        Returns:
            Node ID
        """
        return self.create_destination_node(
            name=name,
            location=location,
            description=description,
            metadata=properties
        )

    def create_destination_node(
        self,
        name: str,
        location: str = "",
        category: str = "",
        description: str = "",
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        创建景点节点

        使用MERGE确保节点唯一性（相同名称不重复创建）

        Args:
            name: 景点名称（唯一标识）
            location: 位置信息
            category: 分类（如：自然景观、历史遗迹）
            description: 描述信息
            metadata: 额外元数据（province, city, filename等）

        Returns:
            节点ID（element ID）

        示例：
            >>> client.create_destination_node(
            ...     name="故宫",
            ...     location="北京市",
            ...     category="历史遗迹",
            ...     metadata={"province": "北京", "city": "北京市"}
            ... )
        """
        if metadata is None:
            metadata = {}

        with self.driver.session() as session:
            query = """
            MERGE (d:Destination {name: $name})
            SET d.location = $location,
                d.category = $category,
                d.description = $description,
                d.province = $province,
                d.city = $city,
                d.filename = $filename,
                d.source = $source,
                d.task_id = $task_id,
                d.created_at = datetime()
            RETURN elementId(d) as id
            """

            result = session.run(
                query,
                name=name,
                location=location,
                category=category,
                description=description,
                province=metadata.get('province', ''),
                city=metadata.get('city', ''),
                filename=metadata.get('filename', ''),
                source=metadata.get('source', ''),
                task_id=metadata.get('task_id', '')
            )

            record = result.single()
            node_id = record['id'] if record else None

            logger.info(f"[Neo4j] Created Destination node: {name} (ID: {node_id})")
            return node_id

    def create_relationship(
        self,
        from_node_id: str,
        to_node_id: str,
        relationship_type: str,
        properties: Optional[Dict[str, Any]] = None
    ):
        """
        Create a relationship between two nodes

        Args:
            from_node_id: Source node element ID
            to_node_id: Target node element ID
            relationship_type: Relationship type (e.g., "RELATED_TO", "LOCATED_IN")
            properties: Relationship properties
        """
        if properties is None:
            properties = {}

        with self.driver.session() as session:
            query = f"""
            MATCH (a), (b)
            WHERE elementId(a) = $from_id AND elementId(b) = $to_id
            MERGE (a)-[r:{relationship_type}]->(b)
            SET r += $props
            RETURN r
            """

            session.run(
                query,
                from_id=from_node_id,
                to_id=to_node_id,
                props=properties
            )

            logger.info(f"[Neo4j] Created relationship: {from_node_id} -{relationship_type}-> {to_node_id}")

    def query_destinations(
        self,
        location: Optional[str] = None,
        category: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Query destinations from Neo4j

        Args:
            location: Filter by location
            category: Filter by category
            limit: Max results

        Returns:
            List of destination nodes
        """
        with self.driver.session() as session:
            conditions = []
            params = {"limit": limit}

            if location:
                conditions.append("d.location CONTAINS $location")
                params["location"] = location

            if category:
                conditions.append("d.category = $category")
                params["category"] = category

            where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""

            query = f"""
            MATCH (d:Destination)
            {where_clause}
            RETURN d.name as name,
                   d.location as location,
                   d.category as category,
                   d.description as description
            LIMIT $limit
            """

            result = session.run(query, **params)
            destinations = []

            for record in result:
                destinations.append({
                    'name': record['name'],
                    'location': record['location'],
                    'category': record['category'],
                    'description': record['description']
                })

            return destinations

    def clear_all(self):
        """Clear all nodes and relationships"""
        with self.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
            logger.warning("[Neo4j] All nodes and relationships cleared")

    def get_node_count(self) -> int:
        """Get total node count"""
        with self.driver.session() as session:
            result = session.run("MATCH (n) RETURN count(n) as count")
            record = result.single()
            return record['count'] if record else 0


# Singleton instance
_neo4j_client = None


def get_neo4j_client() -> Neo4jClient:
    """Get Neo4j client singleton"""
    global _neo4j_client
    if _neo4j_client is None:
        _neo4j_client = Neo4jClient()
    return _neo4j_client
