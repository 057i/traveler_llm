"""
Document Processing Workflow Graph Builder

6-step workflow for document processing pipeline:
1. MinIO存储
2. PDF解析 (MinerU)
3. 文本分块
4. 实体提取
5. RAG向量化 (Milvus)
6. GraphRAG (Neo4j)
"""
from langgraph.graph import StateGraph, END
from loguru import logger

from .state import DocumentProcessingState
from .nodes import (
    save_to_minio,
    minio_fallback,
    parse_pdf_mineru,
    parse_pdf_pypdf,
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
    """6-step document processing workflow graph builder"""

    def __init__(self):
        self.graph = StateGraph(DocumentProcessingState)

    def build(self):
        """
        Build 6-step document processing workflow

        Flow:
        1. save_to_minio → MinIO存储
        2. parse_pdf_mineru → PDF解析 (MinerU API)
        3. chunk_text → 文本分块 (LangChain)
        4. extract_entities → 实体提取 (Qwen LLM)
        5. vectorize_traditional → RAG向量化 (Milvus)
        6. vectorize_graph → GraphRAG (Neo4j)
        7. finalize → 完成并统计
        """
        logger.info("[GraphBuilder] Building 6-step workflow")

        # Step 1: MinIO存储
        self.graph.add_node("save_to_minio", save_to_minio)
        self.graph.add_node("minio_fallback", minio_fallback)

        # Step 2: PDF解析
        self.graph.add_node("parse_pdf_mineru", parse_pdf_mineru)
        self.graph.add_node("parse_fallback", parse_pdf_pypdf)

        # Step 3: 文本分块
        self.graph.add_node("chunk_text", chunk_text)

        # Step 4: 实体提取
        self.graph.add_node("extract_entities", extract_entities)
        self.graph.add_node("extract_fallback", extract_fallback)

        # Step 5: RAG向量化
        self.graph.add_node("vectorize_traditional", vectorize_traditional)
        self.graph.add_node("vector_fallback", vector_fallback)

        # Step 6: GraphRAG
        self.graph.add_node("vectorize_graph", vectorize_graph)
        self.graph.add_node("graph_vector_fallback", graph_vector_fallback)

        # Step 7: 完成
        self.graph.add_node("finalize", finalize)

        # 设置入口点
        self.graph.set_entry_point("save_to_minio")

        # 连接节点 - 6步骤流程
        # Step 1: MinIO存储
        self.graph.add_conditional_edges(
            "save_to_minio",
            self._check_minio_result,
            {
                "success": "parse_pdf_mineru",
                "fallback": "minio_fallback"
            }
        )
        self.graph.add_edge("minio_fallback", "parse_pdf_mineru")

        # Step 2: PDF解析
        self.graph.add_conditional_edges(
            "parse_pdf_mineru",
            self._check_parse_result,
            {
                "success": "chunk_text",
                "fallback": "parse_fallback"
            }
        )
        self.graph.add_edge("parse_fallback", "chunk_text")

        # Step 3: 文本分块 → Step 4: 实体提取
        self.graph.add_edge("chunk_text", "extract_entities")

        # Step 4: 实体提取
        self.graph.add_conditional_edges(
            "extract_entities",
            self._check_extract_result,
            {
                "success": "vectorize_traditional",
                "fallback": "extract_fallback"
            }
        )
        self.graph.add_edge("extract_fallback", "vectorize_traditional")

        # Step 5: RAG向量化
        self.graph.add_conditional_edges(
            "vectorize_traditional",
            self._check_vector_result,
            {
                "success": "vectorize_graph",
                "fallback": "vector_fallback"
            }
        )
        self.graph.add_edge("vector_fallback", "vectorize_graph")

        # Step 6: GraphRAG
        self.graph.add_conditional_edges(
            "vectorize_graph",
            self._check_graph_vector_result,
            {
                "success": "finalize",
                "fallback": "graph_vector_fallback"
            }
        )
        self.graph.add_edge("graph_vector_fallback", "finalize")

        # Step 7: 完成
        self.graph.add_edge("finalize", END)

        # 编译图
        compiled_graph = self.graph.compile()
        logger.success("[GraphBuilder] 6-step workflow compiled successfully")

        return compiled_graph

    def _check_minio_result(self, state: DocumentProcessingState) -> str:
        """Check MinIO save result"""
        return "success" if state.get("minio_success") else "fallback"

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
