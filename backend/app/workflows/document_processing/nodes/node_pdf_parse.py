"""
Node: PDF Parse with MinerU

Uses official MinerU API client for document parsing
"""
from loguru import logger
from ..state import DocumentProcessingState
import os
from app.utils.sse_utils import send_node_start, send_node_end

FLOW_TYPE = "document"


# ==================== 步骤函数 ====================

def step1_get_pdf_pages(file_path: str) -> int:
    """
    Step 1: 获取PDF页数

    Args:
        file_path: PDF文件路径

    Returns:
        页数（失败返回0）
    """
    try:
        import PyPDF2
        with open(file_path, 'rb') as pdf_file:
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            pages_count = len(pdf_reader.pages)
            logger.info(f"[PDF] PDF页数: {pages_count}")
            return pages_count
    except Exception as e:
        logger.warning(f"[PDF] 无法获取页数: {e}")
        return 0


def step2_call_mineru_api(file_path: str, pages_count: int) -> dict:
    """
    Step 2: 调用MinerU API解析PDF (使用V2客户端)

    Args:
        file_path: PDF文件路径
        pages_count: PDF页数

    Returns:
        解析结果字典
    """
    from app.core.mineru_client_v2 import get_mineru_client_v2

    logger.info(f"[PDF] 调用MinerU V2 API解析PDF...")

    # 检查页数限制
    if pages_count > 20:
        logger.warning(f"[PDF] PDF有{pages_count}页，超过API限制，只解析前20页")

    mineru = get_mineru_client_v2()
    result = mineru.parse_by_file(file_path, timeout=600)

    logger.success(f"[PDF] MinerU V2 API调用成功")
    return result


def step3_extract_markdown(result: dict, state_pages_count: int) -> tuple:
    """
    Step 3: 从MinerU V2结果中提取Markdown内容和页数，并清洗文本

    Args:
        result: MinerU V2 API返回结果
        state_pages_count: state中已有的页数（从上传时获取）

    Returns:
        (markdown_text, pages_count)
    """
    from app.utils.text_cleaner import clean_text_for_rag

    # V2客户端已经处理好数据，直接提取
    markdown_text = result.get('markdown', '')
    pages_count = result.get('pages_count', state_pages_count)

    logger.info(f"[PDF] 提取的Markdown长度: {len(markdown_text)} 字符")
    logger.info(f"[PDF] 页数: {pages_count}")

    # 清洗文本
    if len(markdown_text) > 0:
        logger.info(f"[PDF] Markdown前500字符:\n{markdown_text[:500]}")

        # 清洗文本：移除多余换行、空格、特殊字符等
        logger.info(f"[PDF] 开始清洗文本...")
        cleaned_text = clean_text_for_rag(markdown_text)

        logger.info(f"[PDF] 清洗后长度: {len(cleaned_text)} 字符")
        logger.info(f"[PDF] 清洗前后对比: {len(markdown_text)} -> {len(cleaned_text)}")

        markdown_text = cleaned_text
    else:
        logger.warning(f"[PDF] Markdown内容为空！")

    return markdown_text, pages_count



# ==================== 主节点函数 ====================

async def parse_pdf_mineru(state: DocumentProcessingState) -> DocumentProcessingState:
    """
    Node: 使用MinerU解析PDF

    流程:
        1. 获取PDF页数（PyPDF2）
        2. 调用MinerU API解析
        3. 提取Markdown内容和页数
        4. 保存到state

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
            step_id="parse",
            step_name="PDF解析",
            progress=30,
            message="正在使用MinerU解析PDF文档..."
        )

    logger.info("[PDF] === Starting PDF parsing ===")

    try:
        file_path = state.get('file_path')
        filename = os.path.basename(file_path)
        logger.info(f"[PDF] Parsing file: {filename}")

        # 验证文件存在
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        # Step 1: 获取PDF页数
        pages_count_local = step1_get_pdf_pages(file_path)

        # Step 2: 调用MinerU API
        result = step2_call_mineru_api(file_path, pages_count_local)

        # Step 3: 提取Markdown和页数
        markdown_text, pages_count = step3_extract_markdown(
            result,
            state.get('pages_count', pages_count_local)
        )

        # 保存结果到state
        state['raw_text'] = markdown_text
        state['markdown_text'] = markdown_text
        state['parsed_text'] = markdown_text
        state['parse_success'] = True
        state['pages_count'] = pages_count

        # 保存MinerU输出包路径（供MinIO上传使用）
        state['mineru_output_dir'] = result.get('output_directory')
        state['mineru_has_package'] = result.get('has_output_package', False)

        logger.success(f"[PDF] === Parsing completed: {len(markdown_text)} 字符, {pages_count} 页 ===")

        # 发送node_end事件
        if task_id:
            await send_node_end(
                task_id=task_id,
                flow_type=FLOW_TYPE,
                step_id="parse",
                step_name="PDF解析",
                progress=30,
                message=f"PDF解析完成 ({len(markdown_text)} 字符)"
            )

    except Exception as e:
        logger.error(f"[PDF] Parsing failed: {e}")
        import traceback
        traceback.print_exc()
        state['parse_success'] = False
        state.setdefault('errors', []).append(f"Parse error: {str(e)}")

    return state


async def parse_fallback(state: DocumentProcessingState) -> DocumentProcessingState:
    """
    Fallback: 解析失败时使用PyPDF2提取文本
    """
    logger.warning("[PDF] Using fallback - PyPDF2 text extraction")

    try:
        file_path = state.get('file_path')

        import PyPDF2
        text = ""
        with open(file_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            for page in reader.pages:
                text += page.extract_text() + "\n"

        state['raw_text'] = text
        state['parsed_text'] = text
        state['parse_success'] = True

        logger.info(f"[PDF] Fallback extraction: {len(text)} characters")

    except Exception as e:
        logger.error(f"[PDF] Fallback failed: {e}")
        state['parse_success'] = False
        state['raw_text'] = ""
        state['parsed_text'] = ""

    return state
