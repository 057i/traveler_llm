"""
Node: Entity Extraction

Extract destinations and entities from text
"""
from loguru import logger
from ..state import DocumentProcessingState


async def extract_entities(state: DocumentProcessingState) -> DocumentProcessingState:
    """
    Step 4: Extract entities with Qwen
    """
    logger.info("[Extract] Extracting entities with Qwen")

    try:
        chunks = state.get('chunks', [])

        if not chunks:
            logger.warning("[Extract] No chunks to extract from")
            state['destinations'] = []
            state['extract_success'] = False
            return state

        from dashscope import Generation
        from config.settings import settings
        import json

        all_destinations = []

        # Process first few chunks
        for i, chunk in enumerate(chunks[:5]):
            prompt = f"""Extract travel destinations from this text. Return JSON array.

Text: {chunk[:500]}

JSON format: [{{"name": "destination", "description": "brief description", "location": "location"}}]
"""

            response = Generation.call(
                model=settings.QWEN_MODEL,
                prompt=prompt,
                api_key=settings.DASHSCOPE_API_KEY
            )

            if response.status_code == 200:
                try:
                    destinations = json.loads(response.output.text)
                    if isinstance(destinations, list):
                        all_destinations.extend(destinations)
                except:
                    pass

        state['destinations'] = all_destinations
        state['extract_success'] = True

        logger.success(f"[Extract] Extracted {len(all_destinations)} destinations")

        # Save to Neo4j if available
        if all_destinations:
            try:
                logger.info("[Extract] Saving graph data to Neo4j...")
                from app.core.neo4j_client import get_neo4j_client

                neo4j = get_neo4j_client()

                for dest in all_destinations:
                    neo4j.create_destination(
                        name=dest.get('name', ''),
                        description=dest.get('description', ''),
                        location=dest.get('location', '')
                    )

                logger.success(f"[Extract] Saved {len(all_destinations)} destinations to Neo4j")

            except Exception as neo4j_error:
                logger.error(f"[Extract] Failed to save to Neo4j: {neo4j_error}")

    except Exception as e:
        logger.error(f"[Extract] Extraction failed: {e}")
        state['destinations'] = []
        state['extract_success'] = False

    return state


async def extract_fallback(state: DocumentProcessingState) -> DocumentProcessingState:
    """
    Fallback: Skip entity extraction
    """
    logger.warning("[Extract] Using fallback - skipping entity extraction")
    state['destinations'] = []
    state['extract_success'] = True
    return state
