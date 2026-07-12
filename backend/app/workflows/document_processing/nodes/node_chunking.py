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
    task_id = state.get('task_id')

    # 发送 node_start 事件
    if task_id:
        from ..utils import send_node_start
        await send_node_start(
            task_id=task_id,
            step_id="chunk",
            step_name="文本分块",
            progress=45,
            message="正在使用LangChain分割文本块..."
        )

    logger.info("[Chunk] Chunking text with RecursiveCharacterTextSplitter")

    try:
        parsed_text = state.get('parsed_text', '')

        if not parsed_text:
            logger.warning("[Chunk] No text to chunk")
            state['chunks'] = []
            return state

        from langchain_text_splitters import RecursiveCharacterTextSplitter

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=1500,  # 增大chunk，减少chunk数量
            chunk_overlap=150,  # 减少重叠
            separators=["\n\n", "\n", "。", "！", "？", " ", ""]  # 中文优化
        )

        chunks = splitter.split_text(parsed_text)
        state['chunks'] = chunks

        logger.success(f"[Chunk] Created {len(chunks)} chunks")

        # 发送 node_end 事件
        if task_id:
            from ..utils import send_node_end
            await send_node_end(
                task_id=task_id,
                step_id="chunk",
                step_name="文本分块",
                progress=45,
                message=f"文本分块完成 ({len(chunks)} 块)"
            )

    except Exception as e:
        logger.error(f"[Chunk] Chunking failed: {e}")
        # Fallback: split by paragraphs
        parsed_text = state.get('parsed_text', '')
        chunks = [p for p in parsed_text.split('\n\n') if p.strip()]
        state['chunks'] = chunks
        logger.warning(f"[Chunk] Using fallback: {len(chunks)} chunks")

    return state
