"""
Core Module - 核心功能模块

包含系统的核心功能组件：
- embedding_service: 向量嵌入服务（稠密向量 + 稀疏向量）
- milvus_hybrid_client: Milvus混合检索客户端
- neo4j_client: Neo4j图数据库客户端
- redis_client: Redis缓存客户端
- minio_client: MinIO对象存储客户端
- mineru_client_v2: MinerU PDF解析客户端
- rerank_client: 重排序服务客户端
- rrf_client: RRF结果融合引擎
- tavily_client: Tavily网络搜索客户端
- fusion_strategies: 多源结果融合策略
- integrated_search_client: 综合搜索客户端
"""
