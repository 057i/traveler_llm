"""
Document Processing Workflow Graph Builder
Build workflow for document processing pipeline
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
    """Document processing workflow graph builder"""

    def __init__(self):
        self.graph = StateGraph(DocumentProcessingState)

    def build(self):
        """
        Build document processing workflow graph

        Flow:
        MinIO save -> PDF parse -> text chunking -> entity extraction -> vectorization -> graph vectorization -> finalize
        Each step has fallback mechanism for error handling
        """
        self._add_nodes()
        self._add_edges()
        return self.graph.compile()

    def _add_nodes(self):
        """Add all nodes to the graph"""
        self.graph.add_node("save_to_minio", save_to_minio)
        self.graph.add_node("minio_fallback", minio_fallback)
        self.graph.add_node("parse_pdf_mineru", parse_pdf_mineru)
        self.graph.add_node("parse_fallback", parse_pdf_pypdf)
        self.graph.add_node("chunk_text", chunk_text)
        self.graph.add_node("extract_entities", extract_entities)
        self.graph.add_node("extract_fallback", extract_fallback)
        self.graph.add_node("vectorize", vectorize_traditional)
        self.graph.add_node("vector_fallback", vector_fallback)
        self.graph.add_node("vectorize_graph", vectorize_graph)
        self.graph.add_node("graph_vector_fallback", graph_vector_fallback)
        self.graph.add_node("finalize", finalize)

    def _add_edges(self):
        """Add all edges to the graph"""
        self.graph.set_entry_point("save_to_minio")

        # MinIO -> PDF Parse
        self.graph.add_conditional_edges(
            "save_to_minio",
            self._check_minio_result,
            {
                "success": "parse_pdf_mineru",
                "fallback": "minio_fallback"
            }
        )

        # MinIO fallback -> PDF Parse
        self.graph.add_edge("minio_fallback", "parse_pdf_mineru")

        # PDF Parse -> Chunk
        self.graph.add_conditional_edges(
            "parse_pdf_mineru",
            self._check_parse_result,
            {
                "success": "chunk_text",
                "fallback": "parse_fallback"
            }
        )

        # PDF fallback -> Chunk
        self.graph.add_edge("parse_fallback", "chunk_text")

        # Chunk -> Extract
        self.graph.add_edge("chunk_text", "extract_entities")

        # Extract -> Vectorize
        self.graph.add_conditional_edges(
            "extract_entities",
            self._check_extract_result,
            {
                "success": "vectorize",
                "fallback": "extract_fallback"
            }
        )

        # Extract fallback -> Vectorize
        self.graph.add_edge("extract_fallback", "vectorize")

        # Vectorize -> check
        self.graph.add_conditional_edges(
            "vectorize",
            self._check_vector_result,
            {
                "success": "vectorize_graph",
                "fallback": "vector_fallback"
            }
        )

        # Vector fallback -> Vectorize graph
        self.graph.add_edge("vector_fallback", "vectorize_graph")

        # Vectorize graph -> check
        self.graph.add_conditional_edges(
            "vectorize_graph",
            self._check_graph_vector_result,
            {
                "success": "finalize",
                "fallback": "graph_vector_fallback"
            }
        )

        # Graph vector fallback -> finalize
        self.graph.add_edge("graph_vector_fallback", "finalize")

        # Finalize -> END
        self.graph.add_edge("finalize", END)

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
    Build and return document processing workflow

    Returns:
        Compiled document processing workflow graph
    """
    builder = DocumentProcessingGraphBuilder()
    return builder.build()
