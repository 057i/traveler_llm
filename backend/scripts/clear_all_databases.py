#!/usr/bin/env python3
"""
清空远程数据库脚本
清空 Milvus、MinIO、Neo4j、Redis 中的所有数据

警告：此操作不可逆，请谨慎使用！
"""

import sys
import os
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from loguru import logger
from config.settings import settings

# 配置日志
logger.remove()
logger.add(sys.stdout, level="INFO")


def clear_milvus():
    """清空Milvus向量数据库"""
    try:
        logger.info("=" * 80)
        logger.info("[1/4] 开始清空 Milvus 向量数据库...")
        logger.info("=" * 80)

        from pymilvus import connections, utility, Collection

        # 连接Milvus
        connections.connect(
            alias="default",
            host=settings.MILVUS_HOST,
            port=settings.MILVUS_PORT
        )
        logger.info(f"✓ 已连接到 Milvus: {settings.MILVUS_HOST}:{settings.MILVUS_PORT}")

        # 列出所有collection
        collections = utility.list_collections()
        logger.info(f"发现 {len(collections)} 个集合: {collections}")

        if not collections:
            logger.info("✓ Milvus中没有集合，无需清理")
            return

        # 删除所有collection
        for collection_name in collections:
            try:
                collection = Collection(collection_name)
                collection.drop()
                logger.success(f"  ✓ 已删除集合: {collection_name}")
            except Exception as e:
                logger.error(f"  ✗ 删除集合 {collection_name} 失败: {e}")

        connections.disconnect("default")
        logger.success("✓ Milvus 清空完成！")

    except Exception as e:
        logger.error(f"✗ 清空 Milvus 失败: {e}")


def clear_minio():
    """清空MinIO对象存储"""
    try:
        logger.info("=" * 80)
        logger.info("[2/4] 开始清空 MinIO 对象存储...")
        logger.info("=" * 80)

        from minio import Minio

        # 连接MinIO
        minio_client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_SECURE
        )
        logger.info(f"✓ 已连接到 MinIO: {settings.MINIO_ENDPOINT}")

        bucket_name = settings.MINIO_BUCKET

        # 检查桶是否存在
        if not minio_client.bucket_exists(bucket_name):
            logger.info(f"✓ 桶 '{bucket_name}' 不存在，无需清理")
            return

        # 列出所有对象
        objects = list(minio_client.list_objects(bucket_name, recursive=True))
        logger.info(f"发现 {len(objects)} 个文件")

        if not objects:
            logger.info("✓ MinIO中没有文件，无需清理")
            return

        # 删除所有对象
        deleted_count = 0
        for obj in objects:
            try:
                minio_client.remove_object(bucket_name, obj.object_name)
                deleted_count += 1
                if deleted_count % 10 == 0:
                    logger.info(f"  已删除 {deleted_count}/{len(objects)} 个文件...")
            except Exception as e:
                logger.error(f"  ✗ 删除文件 {obj.object_name} 失败: {e}")

        logger.success(f"✓ MinIO 清空完成！共删除 {deleted_count} 个文件")

    except Exception as e:
        logger.error(f"✗ 清空 MinIO 失败: {e}")


def clear_neo4j():
    """清空Neo4j图数据库"""
    try:
        logger.info("=" * 80)
        logger.info("[3/4] 开始清空 Neo4j 图数据库...")
        logger.info("=" * 80)

        from neo4j import GraphDatabase

        # 连接Neo4j
        driver = GraphDatabase.driver(
            settings.NEO4J_URI,
            auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
        )
        logger.info(f"✓ 已连接到 Neo4j: {settings.NEO4J_URI}")

        with driver.session() as session:
            # 统计节点和关系数量
            result = session.run("MATCH (n) RETURN count(n) as node_count")
            node_count = result.single()["node_count"]

            result = session.run("MATCH ()-[r]->() RETURN count(r) as rel_count")
            rel_count = result.single()["rel_count"]

            logger.info(f"发现 {node_count} 个节点，{rel_count} 个关系")

            if node_count == 0 and rel_count == 0:
                logger.info("✓ Neo4j中没有数据，无需清理")
                driver.close()
                return

            # 删除所有节点和关系
            logger.info("正在删除所有节点和关系...")
            session.run("MATCH (n) DETACH DELETE n")

            # 验证删除结果
            result = session.run("MATCH (n) RETURN count(n) as count")
            remaining = result.single()["count"]

            if remaining == 0:
                logger.success(f"✓ Neo4j 清空完成！已删除 {node_count} 个节点和 {rel_count} 个关系")
            else:
                logger.warning(f"⚠ Neo4j 清空不完全，还剩 {remaining} 个节点")

        driver.close()

    except Exception as e:
        logger.error(f"✗ 清空 Neo4j 失败: {e}")


def clear_redis():
    """清空Redis缓存"""
    try:
        logger.info("=" * 80)
        logger.info("[4/4] 开始清空 Redis 缓存...")
        logger.info("=" * 80)

        import redis

        # 连接Redis
        redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            password=settings.REDIS_PASSWORD if settings.REDIS_PASSWORD else None,
            decode_responses=True
        )
        logger.info(f"✓ 已连接到 Redis: {settings.REDIS_HOST}:{settings.REDIS_PORT}")

        # 统计key数量
        key_count = redis_client.dbsize()
        logger.info(f"发现 {key_count} 个键")

        if key_count == 0:
            logger.info("✓ Redis中没有数据，无需清理")
            return

        # 清空当前数据库
        redis_client.flushdb()

        # 验证删除结果
        remaining = redis_client.dbsize()
        if remaining == 0:
            logger.success(f"✓ Redis 清空完成！已删除 {key_count} 个键")
        else:
            logger.warning(f"⚠ Redis 清空不完全，还剩 {remaining} 个键")

    except Exception as e:
        logger.error(f"✗ 清空 Redis 失败: {e}")


def main():
    """主函数"""
    logger.warning("=" * 80)
    logger.warning("⚠️  警告：此操作将清空所有数据库中的数据，不可恢复！")
    logger.warning("=" * 80)

    # 二次确认
    try:
        confirm = input("\n请输入 'YES' 确认清空所有数据: ")
        if confirm != "YES":
            logger.info("操作已取消")
            return
    except KeyboardInterrupt:
        logger.info("\n操作已取消")
        return

    logger.info("\n开始清空数据...")
    logger.info("")

    # 按顺序清空各个数据库
    clear_milvus()
    print()

    clear_minio()
    print()

    clear_neo4j()
    print()

    clear_redis()
    print()

    logger.info("=" * 80)
    logger.success("✓ 所有数据库清空完成！")
    logger.info("=" * 80)


if __name__ == "__main__":
    main()
