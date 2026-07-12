"""
Node: Text Chunking

Split text into manageable chunks
"""
from loguru import logger
from ..state import DocumentProcessingState


async def chunk_text(state: DocumentProcessingState) -> DocumentProcessingState:
    """
    Step 3: Chunk text
    """
    logger.info("[Chunk] Chunking text with RecursiveCharacterTextSplitter")

    try:
        parsed_text = state.get('parsed_text', '')

        if not parsed_text:
            logger.warning("[Chunk] No text to chunk")
            state['chunks'] = []
            return state

        from langchain.text_splitter import RecursiveCharacterTextSplitter

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )

        chunks = splitter.split_text(parsed_text)
        state['chunks'] = chunks

        logger.success(f"[Chunk] Created {len(chunks)} chunks")

    except Exception as e:
        logger.error(f"[Chunk] Chunking failed: {e}")
        # Fallback: split by paragraphs
        parsed_text = state.get('parsed_text', '')
        chunks = [p for p in parsed_text.split('\n\n') if p.strip()]
        state['chunks'] = chunks
        logger.warning(f"[Chunk] Using fallback: {len(chunks)} chunks")

    return state
