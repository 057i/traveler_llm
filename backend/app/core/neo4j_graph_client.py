"""Neo4j Graph Client"""
from neo4j import GraphDatabase
from typing import List, Dict, Any, Optional
from loguru import logger

from config.settings import settings


class Neo4jGraphClient:
    """Neo4j graph database client"""

    def __init__(self):
        self.uri = settings.NEO4J_URI
        self.user = settings.NEO4J_USER
        self.password = settings.NEO4J_PASSWORD
        self.driver = None

    def connect(self):
        """Connect to Neo4j"""
        try:
            self.driver = GraphDatabase.driver(
                self.uri,
                auth=(self.user, self.password)
            )
            self.driver.verify_connectivity()
            logger.success(f"Connected to Neo4j: {self.uri}")
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            raise

    def close(self):
        """Close connection"""
        if self.driver:
            self.driver.close()
            logger.info("Neo4j connection closed")

    def execute_query(self, query: str, parameters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Execute Cypher query"""
        if not self.driver:
            raise Exception("Driver not initialized")

        with self.driver.session() as session:
            result = session.run(query, parameters or {})
            records = [record.data() for record in result]
            return records

    def create_destination_node(self, destination: Dict[str, Any]) -> str:
        """Create destination node"""
        query = """
        MERGE (d:Destination {name: $name})
        SET d.location = $location,
            d.description = $description,
            d.tags = $tags,
            d.rating = $rating
        RETURN d.name as name
        """

        result = self.execute_query(query, {
            "name": destination["name"],
            "location": destination.get("location", ""),
            "description": destination.get("description", ""),
            "tags": destination.get("tags", []),
            "rating": destination.get("rating", 0.0)
        })

        return result[0]["name"] if result else None

    def create_relationship(self, from_node: str, to_node: str, rel_type: str, properties: Dict[str, Any] = None):
        """Create relationship between nodes"""
        query = f"""
        MATCH (a:Destination {{name: $from_name}})
        MATCH (b:Destination {{name: $to_name}})
        MERGE (a)-[r:{rel_type}]->(b)
        """

        if properties:
            set_clause = ", ".join([f"r.{key} = ${key}" for key in properties.keys()])
            query += f" SET {set_clause}"

        query += " RETURN r"

        params = {
            "from_name": from_node,
            "to_name": to_node,
            **(properties or {})
        }

        self.execute_query(query, params)

    def find_similar_destinations(self, destination_name: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Find similar destinations"""
        query = """
        MATCH (d:Destination {name: $name})-[:SIMILAR_TO]-(similar:Destination)
        RETURN similar.name as name,
               similar.location as location,
               similar.description as description,
               similar.tags as tags,
               similar.rating as rating
        LIMIT $limit
        """

        return self.execute_query(query, {"name": destination_name, "limit": limit})

    def find_path(self, from_name: str, to_name: str, max_hops: int = 3) -> List[Dict[str, Any]]:
        """Find path between two destinations"""
        query = f"""
        MATCH path = shortestPath(
            (start:Destination {{name: $from_name}})-[*1..{max_hops}]-(end:Destination {{name: $to_name}})
        )
        RETURN nodes(path) as nodes, relationships(path) as relationships
        """

        return self.execute_query(query, {"from_name": from_name, "to_name": to_name})

    def get_destination_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Get destination by name"""
        query = """
        MATCH (d:Destination {name: $name})
        RETURN d.name as name,
               d.location as location,
               d.description as description,
               d.tags as tags,
               d.rating as rating
        """

        result = self.execute_query(query, {"name": name})
        return result[0] if result else None

    def delete_all(self):
        """Delete all nodes and relationships"""
        query = "MATCH (n) DETACH DELETE n"
        self.execute_query(query)
        logger.warning("Deleted all nodes and relationships")


_neo4j_client = None


def get_neo4j_graph_client() -> Neo4jGraphClient:
    """Get singleton Neo4j graph client instance"""
    global _neo4j_client
    if _neo4j_client is None:
        _neo4j_client = Neo4jGraphClient()
        _neo4j_client.connect()
    return _neo4j_client
