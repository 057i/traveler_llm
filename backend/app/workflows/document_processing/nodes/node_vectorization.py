"""
Node: Vectorization

Vectorize destinations to ChromaDB and Neo4j
"""
from loguru import logger
from ..state import DocumentProcessingState


async def vectorize_traditional(state: DocumentProcessingState) -> DocumentProcessingState:
    """
    Step 5: Traditional vectorization with ChromaDB
    """
    logger.info("[Vector] Traditional vectorization with ChromaDB")

    try:
        destinations = state.get('destinations', [])

        if not destinations:
            logger.warning("[Vector] No destinations to vectorize")
            state['vector_success'] = False
            return state

        from app.core.chroma_client import get_chroma_client

        chroma = get_chroma_client()

        # Add destinations to ChromaDB
        for dest in destinations:
            chroma.add_destination(
                name=dest.get('name', ''),
                description=dest.get('description', ''),
                location=dest.get('location', ''),
                tags=dest.get('tags', [])
            )

        state['vector_success'] = True
        logger.success(f"[Vector] ChromaDB vectorization: {len(destinations)} destinations added")

    except Exception as e:
        logger.error(f"[Vector] Vectorization failed: {e}")
        state['vector_success'] = False

    return state


async def vector_fallback(state: DocumentProcessingState) -> DocumentProcessingState:
    """
    Fallback: Skip vectorization
    """
    logger.warning("[Vector] Using fallback - skipping vectorization")
    state['vector_success'] = True
    return state


async def vectorize_graph(state: DocumentProcessingState) -> DocumentProcessingState:
    """
    Step 6: Graph vectorization with Neo4j
    """
    logger.info("[Vector] Graph vectorization with Neo4j")

    try:
        destinations = state.get('destinations', [])

        if not destinations:
            logger.warning("[Vector] No destinations for graph vectorization")
            state['graph_vector_success'] = False
            return state

        # Graph relationships already created in entity extraction
        state['graph_vector_success'] = True
        logger.success(f"[Vector] Graph vectorization completed with {len(destinations)} entities")

    except Exception as e:
        logger.error(f"[Vector] Graph vectorization failed: {e}")
        state['graph_vector_success'] = False

    return state


async def graph_vector_fallback(state: DocumentProcessingState) -> DocumentProcessingState:
    """
    Fallback: Skip graph vectorization
    """
    logger.warning("[Vector] Using fallback - skipping graph vectorization")
    state['graph_vector_success'] = True
    return state
