"""
Document Processing Workflow Graph Builder

7-step workflow for document processing pipeline:
1. PDF解析 (MinerU) - 先解析
2. MinIO存储 - 上传解析结果
3. 文本分块
4. 实体提取
5. RAG向量化 (Milvus) + GraphRAG (Neo4j) - 并行执行
6. 完成 - 保存元数据和清理临时文件
"""
from langgraph.graph import StateGraph, END
from loguru import logger

from .state import DocumentProcessingState
from .nodes import (
    parse_pdf_mineru,
    parse_fallback,
    upload_to_minio_after_parse,
    minio_upload_fallback,
    chunk_text,
    extract_entities,
    extract_fallback,
    vectorize_traditional,
    vectorize_graph,
    vector_fallback,
    graph_vector_fallback,
    finalize,
)


class DocumentProcessingGraphBuilder:
    """7-step document processing workflow graph builder with parallel vectorization"""

    def __init__(self):
        self.graph = StateGraph(DocumentProcessingState)

    def build(self):
        """
        Build 7-step document processing workflow

        Flow:
        1. parse_pdf_mineru → PDF解析 (MinerU API)
        2. upload_to_minio_after_parse → 上传到MinIO
        3. chunk_text → 文本分块 (LangChain)
        4. extract_entities → 实体提取 (Qwen LLM)
        5. vectorize_traditional + vectorize_graph → RAG向量化和GraphRAG并行
        6. finalize → 完成并保存元数据
        """
        logger.info("[GraphBuilder] Building workflow with new MinIO upload order")

        # Step 1: PDF解析（移到第一步）
        self.graph.add_node("parse_pdf_mineru", parse_pdf_mineru)
        self.graph.add_node("parse_fallback", parse_fallback)

        # Step 2: MinIO存储（移到解析之后）
        self.graph.add_node("upload_to_minio_after_parse", upload_to_minio_after_parse)
        self.graph.add_node("minio_upload_fallback", minio_upload_fallback)

        # Step 3: 文本分块
        self.graph.add_node("chunk_text", chunk_text)

        # Step 4: 实体提取
        self.graph.add_node("extract_entities", extract_entities)
        self.graph.add_node("extract_fallback", extract_fallback)

        # Step 5: RAG向量化 (并行)
        self.graph.add_node("vectorize_traditional", vectorize_traditional)
        self.graph.add_node("vector_fallback", vector_fallback)

        # Step 5: GraphRAG (并行)
        self.graph.add_node("vectorize_graph", vectorize_graph)
        self.graph.add_node("graph_vector_fallback", graph_vector_fallback)

        # Step 6: 完成
        self.graph.add_node("finalize", finalize)

        # 设置入口点 - 改为PDF解析
        self.graph.set_entry_point("parse_pdf_mineru")

        # 连接节点
        # Step 1: PDF解析
        self.graph.add_conditional_edges(
            "parse_pdf_mineru",
            self._check_parse_result,
            {
                "success": "upload_to_minio_after_parse",  # 成功后上传MinIO
                "fallback": "parse_fallback"
            }
        )
        self.graph.add_edge("parse_fallback", "upload_to_minio_after_parse")

        # Step 2: 上传MinIO
        self.graph.add_conditional_edges(
            "upload_to_minio_after_parse",
            self._check_minio_upload_result,
            {
                "success": "chunk_text",
                "fallback": "minio_upload_fallback"
            }
        )
        self.graph.add_edge("minio_upload_fallback", "chunk_text")

        # Step 3: 文本分块 → Step 4: 实体提取
        self.graph.add_edge("chunk_text", "extract_entities")

        # Step 4: 实体提取 → Step 5: 并行向量化
        # extract_entities成功后，同时启动RAG和GraphRAG
        self.graph.add_conditional_edges(
            "extract_entities",
            self._check_extract_result,
            {
                "success": "vectorize_traditional",  # 先到RAG
                "fallback": "extract_fallback"
            }
        )
        # 从extract_entities同时触发GraphRAG（并行）
        self.graph.add_edge("extract_entities", "vectorize_graph")

        # fallback也启动并行向量化
        self.graph.add_edge("extract_fallback", "vectorize_traditional")
        self.graph.add_edge("extract_fallback", "vectorize_graph")

        # Step 5: RAG向量化的fallback
        self.graph.add_conditional_edges(
            "vectorize_traditional",
            self._check_vector_result,
            {
                "success": "finalize",
                "fallback": "vector_fallback"
            }
        )
        self.graph.add_edge("vector_fallback", "finalize")

        # Step 5: GraphRAG的fallback
        self.graph.add_conditional_edges(
            "vectorize_graph",
            self._check_graph_vector_result,
            {
                "success": "finalize",
                "fallback": "graph_vector_fallback"
            }
        )
        self.graph.add_edge("graph_vector_fallback", "finalize")

        # Step 6: 完成
        self.graph.add_edge("finalize", END)

        # 编译图
        compiled_graph = self.graph.compile()
        logger.success("[GraphBuilder] Workflow with new MinIO upload order compiled successfully")

        return compiled_graph

    def _check_minio_result(self, state: DocumentProcessingState) -> str:
        """Check MinIO save result (旧的，保留兼容)"""
        return "success" if state.get("minio_success") else "fallback"

    def _check_minio_upload_result(self, state: DocumentProcessingState) -> str:
        """Check MinIO upload result (新的，解析后上传)"""
        return "success" if state.get("minio_upload_success") else "fallback"

    def _check_parse_result(self, state: DocumentProcessingState) -> str:
        """Check PDF parse result"""
        return "success" if state.get("parse_success") else "fallback"

    def _check_extract_result(self, state: DocumentProcessingState) -> str:
        """Check entity extraction result"""
        return "success" if state.get("extract_success") else "fallback"

    def _check_vector_result(self, state: DocumentProcessingState) -> str:
        """Check vectorization result"""
        return "success" if state.get("vector_success") else "fallback"

    def _check_graph_vector_result(self, state: DocumentProcessingState) -> str:
        """Check graph vectorization result"""
        return "success" if state.get("graph_vector_success") else "fallback"


def build_document_processing_workflow():
    """
    Build and return 6-step document processing workflow

    Returns:
        Compiled 6-step workflow graph
    """
    builder = DocumentProcessingGraphBuilder()
    return builder.build()
