"""
RRF Fusion Workflow
Reciprocal Rank Fusion for multi-source retrieval
"""
from typing import List, Dict, Any
from loguru import logger


class RRFWorkflow:
    """RRF fusion workflow"""

    def __init__(self, k: int = 60):
        """
        Initialize RRF workflow

        Args:
            k: RRF constant (default: 60)
        """
        self.k = k

    async def fuse(
        self,
        vector_results: List[Dict[str, Any]],
        graph_results: List[Dict[str, Any]] = None,
        top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Fuse multiple ranked lists using RRF algorithm

        Args:
            vector_results: Results from vector database
            graph_results: Results from knowledge graph (optional)
            top_k: Number of top results to return

        Returns:
            Fused and re-ranked results
        """
        logger.info("[RRF] Starting fusion...")

        try:
            scores = {}

            # Process vector results
            for rank, result in enumerate(vector_results, start=1):
                doc_id = self._get_doc_id(result)
                rrf_score = 1.0 / (self.k + rank)

                if doc_id in scores:
                    scores[doc_id]['score'] += rrf_score
                    scores[doc_id]['sources'].append('vector')
                else:
                    scores[doc_id] = {
                        'id': doc_id,
                        'content': result.get('content', ''),
                        'score': rrf_score,
                        'sources': ['vector'],
                        'metadata': result.get('metadata', {}),
                        'original_data': result
                    }

            # Process graph results if provided
            if graph_results:
                for rank, result in enumerate(graph_results, start=1):
                    doc_id = self._get_doc_id(result)
                    rrf_score = 1.0 / (self.k + rank)

                    if doc_id in scores:
                        scores[doc_id]['score'] += rrf_score
                        if 'graph' not in scores[doc_id]['sources']:
                            scores[doc_id]['sources'].append('graph')
                    else:
                        scores[doc_id] = {
                            'id': doc_id,
                            'content': result.get('content', ''),
                            'score': rrf_score,
                            'sources': ['graph'],
                            'metadata': result.get('metadata', {}),
                            'original_data': result
                        }

            # Sort by RRF score
            fused_results = sorted(
                scores.values(),
                key=lambda x: x['score'],
                reverse=True
            )[:top_k]

            logger.success(
                f"[RRF] Fused {len(vector_results)} vector + "
                f"{len(graph_results) if graph_results else 0} graph results "
                f"-> {len(fused_results)} final results"
            )

            return fused_results

        except Exception as e:
            logger.error(f"[RRF] Fusion failed: {e}")
            # Fallback to vector results only
            return vector_results[:top_k]

    def _get_doc_id(self, result: Dict[str, Any]) -> str:
        """
        Extract document ID from result

        Args:
            result: Search result dictionary

        Returns:
            Document ID string
        """
        # Try multiple possible ID fields
        if 'id' in result:
            return str(result['id'])
        elif 'doc_id' in result:
            return str(result['doc_id'])
        elif 'content' in result:
            # Use content hash as ID if no explicit ID
            return str(hash(result['content']))
        else:
            # Last resort: use string representation
            return str(hash(str(result)))

    async def rerank(
        self,
        results: List[Dict[str, Any]],
        query: str,
        use_llm: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Optional: Re-rank fused results using LLM

        Args:
            results: Fused results
            query: Original query
            use_llm: Whether to use LLM for re-ranking

        Returns:
            Re-ranked results
        """
        if not use_llm:
            return results

        logger.info("[RRF] Re-ranking with LLM...")

        try:
            from app.services.qwen_service import get_qwen_service

            qwen = get_qwen_service()

            # Build re-ranking prompt
            docs_text = "\n\n".join([
                f"Document {i+1}:\n{r['content'][:200]}"
                for i, r in enumerate(results[:10])
            ])

            rerank_prompt = f"""Given the user query and the following documents,
rank them by relevance. Return only the document numbers in order (e.g., "3,1,5,2,4").

Query: {query}

{docs_text}

Ranking:"""

            response = await qwen.chat(rerank_prompt)

            # Parse ranking
            try:
                ranking = [int(x.strip()) - 1 for x in response.strip().split(',')]
                reranked = [results[i] for i in ranking if 0 <= i < len(results)]

                # Add remaining docs not in ranking
                ranked_indices = set(ranking)
                for i, result in enumerate(results):
                    if i not in ranked_indices:
                        reranked.append(result)

                logger.success(f"[RRF] Re-ranked {len(reranked)} results with LLM")
                return reranked

            except:
                logger.warning("[RRF] Failed to parse LLM ranking, using original order")
                return results

        except Exception as e:
            logger.error(f"[RRF] Re-ranking failed: {e}")
            return results


# Singleton instance
_workflow_instance = None


def get_rrf_workflow(k: int = 60) -> RRFWorkflow:
    """Get workflow singleton"""
    global _workflow_instance
    if _workflow_instance is None:
        _workflow_instance = RRFWorkflow(k=k)
    return _workflow_instance
