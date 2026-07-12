"""
Node: PDF Parse with MinerU

Uses official MinerU API client for document parsing
"""
from loguru import logger
from ..state import DocumentProcessingState
import os


async def parse_pdf_mineru(state: DocumentProcessingState) -> DocumentProcessingState:
    """
    Step 2: Parse PDF with MinerU

    Uses official MinerU API to convert PDF to high-quality Markdown
    """
    task_id = state.get('task_id')

    # 发送 node_start 事件
    if task_id:
        from ..utils import send_node_start
        await send_node_start(
            task_id=task_id,
            step_id="parse",
            step_name="PDF解析",
            progress=30,
            message="正在使用MinerU解析PDF文档..."
        )

    logger.info("[PDF] Starting PDF parse with MinerU")

    try:
        file_path = state.get('file_path')
        filename = os.path.basename(file_path)
        logger.info(f"[PDF] Parsing file: {filename}")

        # Check if file exists
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        # Get PDF page count
        pages_count = 0
        try:
            import PyPDF2
            with open(file_path, 'rb') as pdf_file:
                pdf_reader = PyPDF2.PdfReader(pdf_file)
                pages_count = len(pdf_reader.pages)
                logger.info(f"[PDF] PDF页数: {pages_count}")
        except Exception as e:
            logger.warning(f"[PDF] 无法获取页数: {e}")

        # Store page count in state
        state['pages_count'] = pages_count

        # Use MinerU client
        from app.core.mineru_client import get_mineru_client

        mineru = get_mineru_client()

        # Parse PDF
        logger.info("[PDF] 调用MinerU API解析PDF...")

        # 如果页数超过20页，只解析前20页
        page_range = None
        if pages_count > 20:
            page_range = "1-20"
            logger.warning(f"[PDF] PDF有{pages_count}页，超过API限制，只解析前20页")

        result = mineru.parse_by_file(
            file_path=file_path,
            language="ch",  # 中文
            enable_table=True,  # 解析表格
            is_ocr=False,  # 如果是扫描件设为True
            enable_formula=True,  # 解析公式
            page_range=page_range  # 页面范围
        )

        if result and isinstance(result, dict):
            markdown_text = result.get('markdown_content', '')

            # 尝试从MinerU结果中获取页数（如果API提供）
            if 'pages_count' in result:
                pages_count = result.get('pages_count', 0)
                logger.info(f"[PDF] MinerU返回页数: {pages_count}")
            else:
                # MinerU API不提供页数，使用state中已有的页数（从上传时获取）
                pages_count = state.get('pages_count', 0)
                if pages_count > 0:
                    logger.info(f"[PDF] 使用上传时获取的页数: {pages_count}")
                else:
                    logger.warning(f"[PDF] 未获取到页数信息，设为0")

            # Store results
            state['raw_text'] = markdown_text
            state['markdown_text'] = markdown_text
            state['parsed_text'] = markdown_text
            state['parse_success'] = True
            state['pages_count'] = pages_count  # 保存页数

            # 保存MinerU输出包路径（供MinIO上传使用）
            state['mineru_output_dir'] = result.get('output_directory')
            state['mineru_has_package'] = result.get('has_output_package', False)

            logger.success(f"[PDF] MinerU解析成功: {len(markdown_text)} 字符, {pages_count} 页")

            # 发送 node_end 事件
            if task_id:
                from ..utils import send_node_end
                await send_node_end(
                    task_id=task_id,
                    step_id="parse",
                    step_name="PDF解析",
                    progress=30,
                    message=f"PDF解析完成 ({len(markdown_text)} 字符)"
                )

            if result.get('has_output_package'):
                logger.info(f"[PDF] MinerU输出包路径: {result['output_directory']}")

        else:
            error_msg = "MinerU API returned empty content"
            logger.error(f"[PDF] {error_msg}")
            state['parse_success'] = False
            state.setdefault('errors', []).append(error_msg)

    except FileNotFoundError as e:
        logger.error(f"[PDF] 文件不存在: {e}")
        state['parse_success'] = False
        state.setdefault('errors', []).append(str(e))

    except Exception as e:
        logger.error(f"[PDF] Parse failed: {e}")
        import traceback
        traceback.print_exc()
        state['parse_success'] = False
        state.setdefault('errors', []).append(f"PDF parse error: {str(e)}")

    return state


async def parse_pdf_pypdf(state: DocumentProcessingState) -> DocumentProcessingState:
    """
    Fallback: No longer used (MinerU only)
    """
    logger.error("[PDF] Fallback不应被调用 - 请确保MinerU API正常运行")

    state['parse_success'] = False
    state.setdefault('errors', []).append("MinerU API失败且无回退方案")

    return state
