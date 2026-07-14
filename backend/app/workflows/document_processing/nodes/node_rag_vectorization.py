"""
Node: RAG Vectorization to Milvus

Store embeddings in Milvus (dense + sparse vectors)
"""
from loguru import logger
from ..state import DocumentProcessingState
from typing import List
import json
import asyncio
from app.utils.sse_utils import send_node_start, send_node_end

FLOW_TYPE = "document"


# ==================== 步骤函数 ====================

def step1_prepare_texts(destinations: list, filename: str) -> tuple:
    """
    Step 1: 准备向量化文本

    Args:
        destinations: 景点列表
        filename: 文件名

    Returns:
        (texts, full_texts) - 基本文本和完整文本
    """
    texts = []
    full_texts = []

    for dest in destinations:
        # 基本文本（用于embedding）
        text = f"{dest.get('name', '')} {dest.get('description', '')} {dest.get('city', '')} {dest.get('province', '')} {' '.join(dest.get('tags', []))}"
        texts.append(text)

        # 完整文本（包含所有信息）
        full_text_parts = [
            f"{dest.get('name', '')}",
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

    logger.info(f"[RAG] Prepared {len(texts)} texts for vectorization")
    return texts, full_texts


def step2_generate_dense_vectors(embedding_service, texts: list) -> list:
    """
    Step 2: 生成稠密向量

    Args:
        embedding_service: Embedding服务
        texts: 文本列表

    Returns:
        稠密向量列表
    """
    logger.info(f"[RAG] Generating dense vectors for {len(texts)} destinations")
    dense_vectors = embedding_service.encode(texts, normalize_embeddings=True)
    logger.success(f"[RAG] Generated {len(dense_vectors)} dense vectors")
    return dense_vectors


def step3_generate_sparse_vectors(embedding_service, texts: list) -> list:
    """
    Step 3: 生成稀疏向量（BM25）

    Args:
        embedding_service: Embedding服务
        texts: 文本列表

    Returns:
        稀疏向量列表
    """
    logger.info(f"[RAG] Generating sparse vectors for {len(texts)} destinations")
    sparse_vectors = embedding_service.encode_sparse(texts)
    logger.success(f"[RAG] Generated {len(sparse_vectors)} sparse vectors")
    return sparse_vectors


def step4_insert_to_milvus(milvus, destinations: list, dense_vectors: list,
                           sparse_vectors: list, full_texts: list, filename: str):
    """
    Step 4: 插入数据到Milvus

    Args:
        milvus: Milvus客户端
        destinations: 景点列表
        dense_vectors: 稠密向量
        sparse_vectors: 稀疏向量
        full_texts: 完整文本
        filename: 文件名
    """
    data = []
    for i, dest in enumerate(destinations):
        # 处理预算字段
        budget_range = dest.get('budget_range', [0, 0])
        estimated_budget = int((budget_range[0] + budget_range[1]) / 2) if budget_range and len(budget_range) == 2 else 200

        # 处理天数字段（从visit_duration提取）
        visit_duration = dest.get('visit_duration', '')
        recommended_days = 1  # 默认1天
        if '天' in visit_duration:
            try:
                import re
                days_match = re.search(r'(\d+)', visit_duration)
                if days_match:
                    recommended_days = int(days_match.group(1))
            except:
                pass

        # 处理旅行类型（优先用category，否则用type）
        travel_type = dest.get('category', dest.get('type', '景点'))

        # 处理标签（确保是列表）
        tags = dest.get('tags', [])
        if not isinstance(tags, list):
            tags = [tags] if tags else []
        if not tags:
            tags = [travel_type] if travel_type else ['景点']

        # 处理季节（确保是列表）
        best_season = dest.get('best_season', [])
        if not isinstance(best_season, list):
            best_season = [best_season] if best_season else []
        if not best_season:
            best_season = ['春', '夏', '秋', '冬']

        data.append({
            "destination_id": dest.get('graph_id', f"dest_{i}"),
            "dense_vector": dense_vectors[i],
            "sparse_vector": sparse_vectors[i],
            "name": dest.get('name', ''),
            "province": dest.get('province', ''),
            "city": dest.get('city', ''),
            "category": dest.get('category', ''),
            "description": dest.get('description', ''),
            "filename": filename,
            "entity_json": json.dumps(dest, ensure_ascii=False),
            "full_text": full_texts[i],
            "rating": dest.get('rating', 0.0),
            # 扩展字段（从提取的数据智能转换）
            "estimated_budget": estimated_budget,
            "recommended_days": recommended_days,
            "travel_type": travel_type,
            "tags": tags,
            "best_season": best_season
        })

    logger.info(f"[RAG] Inserting {len(data)} entries to Milvus")

    # 调试：打印第一条数据的字段（使用info级别确保显示）
    if data:
        first_entry = data[0]
        logger.info(f"[RAG] First entry fields: {list(first_entry.keys())}")
        logger.info(f"[RAG] First entry field count: {len(first_entry)}")
        logger.info(f"[RAG] Expected: 17 fields")

    milvus.insert(data)
    logger.success(f"[RAG] Successfully inserted to Milvus")


# ==================== 主节点函数 ====================

async def vectorize_traditional(state: DocumentProcessingState) -> DocumentProcessingState:
    """
    Node: RAG向量化到Milvus（稠密 + 稀疏）

    流程:
        1. 准备向量化文本
        2. 生成稠密向量（BGE + 归一化）
        3. 生成稀疏向量（BM25）
        4. 插入到Milvus

    Args:
        state: 工作流状态

    Returns:
        更新后的状态
    """
    task_id = state.get('task_id')

    # 发送node_start事件
    if task_id:
        await send_node_start(
            task_id=task_id,
            flow_type=FLOW_TYPE,
            step_id="vectorize_traditional",
            step_name="RAG向量化",
            progress=75,
            message="正在向量化到Milvus数据库..."
        )

    logger.info("[RAG] === Starting RAG vectorization (dense + sparse) ===")

    try:
        destinations = state.get('destinations', [])
        filename = state.get('filename', 'unknown.pdf')

        if not destinations:
            logger.warning("[RAG] No destinations to vectorize")
            state['vector_success'] = False
            return state

        # 加载服务
        from app.core.embedding_service import get_embedding_service
        from app.core.milvus_hybrid_client import get_milvus_hybrid_client

        embedding_service = get_embedding_service()
        milvus = get_milvus_hybrid_client()

        # Step 1: 准备文本
        texts, full_texts = step1_prepare_texts(destinations, filename)

        # Step 2: 生成稠密向量（在线程池中执行，避免阻塞事件循环）
        logger.info("[RAG] Running dense vectorization in thread pool...")
        loop = asyncio.get_event_loop()
        dense_vectors = await loop.run_in_executor(
            None,  # 使用默认线程池
            step2_generate_dense_vectors,
            embedding_service,
            texts
        )

        # Step 3: 生成稀疏向量（在线程池中执行）
        logger.info("[RAG] Running sparse vectorization in thread pool...")
        sparse_vectors = await loop.run_in_executor(
            None,
            step3_generate_sparse_vectors,
            embedding_service,
            texts
        )

        # Step 4: 插入到Milvus（IO操作，可以直接调用）
        step4_insert_to_milvus(
            milvus, destinations, dense_vectors,
            sparse_vectors, full_texts, filename
        )

        state['vector_success'] = True
        logger.success(
            f"[RAG] === RAG vectorization completed: {len(destinations)} destinations ==="
        )

        # 发送node_end事件
        if task_id:
            await send_node_end(
                task_id=task_id,
                flow_type=FLOW_TYPE,
                step_id="vectorize_traditional",
                step_name="RAG向量化",
                progress=75,
                message=f"RAG向量化完成 ({len(destinations)} 个景点)"
            )

        # 并行节点只返回自己修改的字段，避免冲突
        return {"vector_success": True}

    except Exception as e:
        logger.error(f"[RAG] Vectorization failed: {e}")
        import traceback
        traceback.print_exc()

        # 并行节点只返回自己修改的字段
        return {
            "vector_success": False,
            "errors": [f"RAG vectorization error: {str(e)}"]
        }


async def vector_fallback(state: DocumentProcessingState) -> DocumentProcessingState:
    """
    Fallback: 跳过RAG向量化
    """
    logger.warning("[RAG] Using fallback - skipping RAG vectorization")
    # 只返回修改的字段，避免并发冲突
    return {"vector_success": True}
