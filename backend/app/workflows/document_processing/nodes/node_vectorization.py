"""
Node: Vectorization

使用混合向量（稠密+稀疏）存储到Milvus和Neo4j
"""
from loguru import logger
from ..state import DocumentProcessingState
import asyncio
import json


async def vectorize_traditional(state: DocumentProcessingState) -> DocumentProcessingState:
    """
    Step 5: 混合向量化到Milvus（稠密向量 + 稀疏向量）

    存储完整的景点信息到Milvus，包括：
    - 稠密向量（bge-base-zh-v1.5）
    - 稀疏向量（BM25）
    - 完整元数据（包括filename和entity_json）
    """
    task_id = state.get('task_id')

    # 发送 node_start 事件
    if task_id:
        from ..utils import send_node_start
        await send_node_start(
            task_id=task_id,
            step_id="vectorize_traditional",
            step_name="传统向量化",
            progress=75,
            message="正在向量化到Milvus数据库..."
        )

    logger.info("[Vector] Hybrid vectorization with Milvus (dense + sparse)")

    try:
        destinations = state.get('destinations', [])
        filename = state.get('filename', 'unknown.pdf')

        if not destinations:
            logger.warning("[Vector] No destinations to vectorize")
            state['vector_success'] = False
            return state

        # 1. 加载服务
        from app.core.embedding_service import get_embedding_service
        from app.core.milvus_hybrid_client import get_milvus_hybrid_client

        embedding_service = get_embedding_service()
        milvus = get_milvus_hybrid_client()

        # 2. 准备文本和完整信息
        texts = []
        full_texts = []

        for dest in destinations:
            # 基本文本（用于embedding）
            text = f"{dest.get('name', '')} {dest.get('description', '')} {dest.get('city', '')} {dest.get('province', '')} {' '.join(dest.get('tags', []))}"
            texts.append(text)

            # 完整文本（包含所有信息，用于检索和展示）
            full_text_parts = [
                f"{dest.get('name', '')}",
                f"类型: {dest.get('type', '景点')}",
                f"分类: {dest.get('category', '')}",
                f"位置: {dest.get('province', '')}{dest.get('city', '')}{dest.get('address', '')}",
                f"描述: {dest.get('description', '')}",
                f"标签: {', '.join(dest.get('tags', []))}",
                f"最佳季节: {', '.join(dest.get('best_season', []))}",
                f"适合人群: {', '.join(dest.get('suitable_for', []))}",
                f"特色: {', '.join(dest.get('features', []))}",
                f"门票: {dest.get('ticket_price', '')}元" if dest.get('ticket_price') else "",
                f"开放时间: {dest.get('opening_hours', '')}",
                f"游玩时长: {dest.get('visit_duration', '')}",
                f"预算: {dest.get('budget_range', [])}",
                f"评分: {dest.get('rating', 0.0)}"
            ]
            full_text = " | ".join([p for p in full_text_parts if p])
            full_texts.append(full_text)

        # 3. 生成稠密向量（预归一化优化）
        logger.info(f"[Vector] Generating dense vectors for {len(texts)} destinations")
        dense_vectors = embedding_service.encode(texts, normalize_embeddings=True)

        # 4. 生成稀疏向量
        logger.info(f"[Vector] Generating sparse vectors for {len(texts)} destinations")
        sparse_vectors = embedding_service.encode_sparse(texts)

        # 5. 准备插入数据
        data = []
        for i, dest in enumerate(destinations):
            data.append({
                "destination_id": dest.get('graph_id', f"dest_{i}"),
                "dense_vector": dense_vectors[i],
                "sparse_vector": sparse_vectors[i],
                "name": dest.get('name', ''),
                "province": dest.get('province', ''),
                "city": dest.get('city', ''),
                "category": dest.get('category', ''),
                "description": dest.get('description', ''),
                "filename": filename,  # 来源文件名
                "entity_json": json.dumps(dest, ensure_ascii=False),  # 完整实体JSON
                "full_text": full_texts[i],
                "rating": dest.get('rating', 0.0)
            })

        # 6. 插入Milvus
        logger.info(f"[Vector] Inserting {len(data)} entries to Milvus")
        milvus.insert(data)

        state['vector_success'] = True
        logger.success(f"[Vector] Hybrid vectorization complete: {len(destinations)} destinations (dense + sparse)")

        # 发送 node_end 事件
        if task_id:
            from ..utils import send_node_end
            await send_node_end(
                task_id=task_id,
                step_id="vectorize_traditional",
                step_name="传统向量化",
                progress=75,
                message=f"RAG向量化完成 ({len(destinations)} 个景点)"
            )

    except Exception as e:
        logger.error(f"[Vector] Vectorization failed: {e}")
        import traceback
        traceback.print_exc()
        state['vector_success'] = False
        state.setdefault('errors', []).append(f"Vectorization error: {str(e)}")

    return state


async def vectorize_graph(state: DocumentProcessingState) -> DocumentProcessingState:
    """
    Step 6: GraphRAG vectorization with Neo4j

    存储destinations和relationships到Neo4j知识图谱
    """
    task_id = state.get('task_id')

    # 发送 node_start 事件
    if task_id:
        from ..utils import send_node_start
        await send_node_start(
            task_id=task_id,
            step_id="vectorize_graph",
            step_name="图向量化",
            progress=90,
            message="正在构建Neo4j知识图谱..."
        )

    logger.info("[Vector] GraphRAG vectorization with Neo4j")

    try:
        destinations = state.get('destinations', [])

        if not destinations:
            logger.warning("[Vector] No destinations for graph vectorization")
            state['graph_vector_success'] = False
            return state

        from app.core.neo4j_client import get_neo4j_client

        neo4j = get_neo4j_client()

        # 添加destinations到Neo4j
        for dest in destinations:
            try:
                neo4j.create_destination(
                    name=dest.get('name', ''),
                    description=dest.get('description', ''),
                    location=f"{dest.get('province', '')}{dest.get('city', '')}",
                    properties=dest
                )

            except Exception as dest_error:
                logger.warning(f"[Vector] Failed to add {dest.get('name', 'Unknown')}: {dest_error}")
                continue

        state['graph_vector_success'] = True
        logger.success(f"[Vector] GraphRAG completed with {len(destinations)} entities")

        # 发送 node_end 事件
        if task_id:
            from ..utils import send_node_end
            await send_node_end(
                task_id=task_id,
                step_id="vectorize_graph",
                step_name="图向量化",
                progress=90,
                message=f"知识图谱构建完成 ({len(destinations)} 个节点)"
            )

    except Exception as e:
        logger.error(f"[Vector] Graph vectorization failed: {e}")
        import traceback
        traceback.print_exc()
        state['graph_vector_success'] = False
        state.setdefault('errors', []).append(f"Graph vectorization error: {str(e)}")

    return state


async def vector_fallback(state: DocumentProcessingState) -> DocumentProcessingState:
    """
    Fallback: Skip vectorization if it fails
    """
    logger.warning("[Vector] Using fallback - skipping vectorization")
    state['vector_success'] = False
    return state


async def graph_vector_fallback(state: DocumentProcessingState) -> DocumentProcessingState:
    """
    Fallback: Skip graph vectorization if it fails
    """
    logger.warning("[Vector] Using fallback - skipping graph vectorization")
    state['graph_vector_success'] = False
    return state


async def vectorize_parallel(state: DocumentProcessingState) -> DocumentProcessingState:
    """
    Parallel execution of RAG and GraphRAG vectorization
    """
    logger.info("[Vector] Starting parallel vectorization (RAG + GraphRAG)")

    # Execute both vectorizations in parallel
    results = await asyncio.gather(
        vectorize_traditional(state),
        vectorize_graph(state),
        return_exceptions=True
    )

    # Check for exceptions
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            logger.error(f"[Vector] Parallel vectorization error: {result}")

    # Merge results
    state.update(results[0])
    state.update(results[1])

    logger.success("[Vector] Parallel vectorization completed")

    return state
