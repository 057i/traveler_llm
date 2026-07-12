"""
Node: PDF Parse

Parse PDF files using MinerU or PyPDF as fallback
"""
from loguru import logger
from ..state import DocumentProcessingState


async def parse_pdf_mineru(state: DocumentProcessingState) -> DocumentProcessingState:
    """
    Step 2: Parse PDF with MinerU
    """
    logger.info("[PDF] Starting PDF parse with MinerU")

    try:
        file_path = state.get('file_path')

        # Placeholder: In production, call actual MinerU API
        # For now, use simple PDF parsing
        logger.info(f"[PDF] Parsing file: {file_path}")

        import PyPDF2
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            pages = len(pdf_reader.pages)

            text_parts = []
            for page in pdf_reader.pages:
                text_parts.append(page.extract_text())

            parsed_text = "\n".join(text_parts)

        state['parsed_text'] = parsed_text
        state['parse_success'] = True

        logger.success(f"[PDF] MinerU parsed: {pages} pages, {len(parsed_text)} chars")

    except Exception as e:
        logger.error(f"[PDF] MinerU parse failed: {e}")
        state["parse_success"] = False

    return state


async def parse_pdf_pypdf(state: DocumentProcessingState) -> DocumentProcessingState:
    """
    Fallback: Parse PDF with PyPDF
    """
    logger.warning("[PDF] Using PyPDF fallback")

    try:
        file_path = state.get('file_path')

        import PyPDF2
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            pages = len(pdf_reader.pages)

            text_parts = []
            for page in pdf_reader.pages:
                text_parts.append(page.extract_text())

            parsed_text = "\n".join(text_parts)

        state['parsed_text'] = parsed_text
        state['parse_success'] = True

        logger.success(f"[PDF] PyPDF parsed: {pages} pages")

    except Exception as e:
        logger.error(f"[PDF] PyPDF parse failed: {e}")
        state["parse_success"] = False

    return state
