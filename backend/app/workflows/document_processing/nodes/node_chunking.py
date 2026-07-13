"""
Node: Text Chunking

Split text into manageable chunks
"""
from loguru import logger
from ..state import DocumentProcessingState
from app.utils.sse_utils import send_node_start, send_node_end

FLOW_TYPE = "document"


# ==================== 步骤函数 ====================

def step1_create_text_splitter():
    """
    Step 1: 创建文本分割器

    Returns:
        RecursiveCharacterTextSplitter实例
    """
    from langchain_text_splitters import RecursiveCharacterTextSplitter

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1500,  # 增大chunk，减少chunk数量
        chunk_overlap=150,  # 减少重叠
        separators=["\n\n", "\n", "。", "！", "？", " ", ""]  # 中文优化
    )

    logger.info(f"[Chunk] Created text splitter (size=1500, overlap=150)")
    return splitter


def step2_split_text(splitter, text: str) -> list:
    """
    Step 2: 分割文本

    Args:
        splitter: 文本分割器
        text: 待分割的文本

    Returns:
        文本块列表
    """
    chunks = splitter.split_text(text)
    logger.success(f"[Chunk] Created {len(chunks)} chunks")
    return chunks


# ==================== 主节点函数 ====================

async def chunk_text(state: DocumentProcessingState) -> DocumentProcessingState:
    """
    Node: 文本分块

    流程:
        1. 创建文本分割器（LangChain RecursiveCharacterTextSplitter）
        2. 分割文本为多个chunk

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
            step_id="chunk",
            step_name="文本分块",
            progress=45,
            message="正在使用LangChain分割文本块..."
        )

    logger.info("[Chunk] === Starting text chunking ===")

    try:
        parsed_text = state.get('parsed_text', '')

        # 验证文本不为空
        if not parsed_text:
            logger.warning("[Chunk] No text to chunk")
            state['chunks'] = []
            return state

        # Step 1: 创建文本分割器
        splitter = step1_create_text_splitter()

        # Step 2: 分割文本
        chunks = step2_split_text(splitter, parsed_text)

        # 保存结果到state
        state['chunks'] = chunks

        logger.success(f"[Chunk] === Chunking completed: {len(chunks)} chunks ===")

        # 发送node_end事件
        if task_id:
            await send_node_end(
                task_id=task_id,
                flow_type=FLOW_TYPE,
                step_id="chunk",
                step_name="文本分块",
                progress=45,
                message=f"文本分块完成 ({len(chunks)} 块)"
            )

    except Exception as e:
        logger.error(f"[Chunk] Chunking failed: {e}")
        # Fallback: 按段落分割
        parsed_text = state.get('parsed_text', '')
        chunks = [p for p in parsed_text.split('\n\n') if p.strip()]
        state['chunks'] = chunks
        logger.warning(f"[Chunk] Using fallback: {len(chunks)} chunks")

    return state
