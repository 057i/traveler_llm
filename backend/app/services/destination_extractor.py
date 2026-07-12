"""
Destination Extractor Service
"""
from typing import List, Optional
from loguru import logger
import dashscope
from dashscope import Generation

from config.settings import settings


class DestinationExtractorService:
    """Extract destination names from user query using LLM"""

    def __init__(self):
        """Initialize extractor service"""
        self.api_key = settings.DASHSCOPE_API_KEY
        dashscope.api_key = self.api_key

    async def extract_destinations(self, query: str) -> List[str]:
        """Extract destination names from query"""
        try:
            prompt = f"""Extract travel destination names from the following user query.
Return ONLY the destination names as a comma-separated list, without any other text.
If no destinations are found, return "NONE".

User query: {query}

Destination names:"""

            response = Generation.call(
                model=settings.LLM_MODEL,
                prompt=prompt,
                max_tokens=100,
                temperature=0.1
            )

            if response.status_code == 200:
                result = response.output.text.strip()

                if result == "NONE" or not result:
                    logger.info(f"No destinations found in query: {query}")
                    return []

                # Parse comma-separated destinations
                destinations = [d.strip() for d in result.split(",") if d.strip()]

                logger.success(f"Extracted {len(destinations)} destinations: {destinations}")
                return destinations
            else:
                logger.error(f"LLM API error: {response.message}")
                return []

        except Exception as e:
            logger.error(f"Failed to extract destinations: {e}")
            return []

    async def extract_core_entities(self, query: str) -> str:
        """Extract core entities from query for better RAG search"""
        try:
            prompt = f"""Extract the core travel-related entities and intent from the user query.
Return a focused search phrase (5-10 words) that captures the key travel aspects.

User query: {query}

Core search phrase:"""

            response = Generation.call(
                model=settings.LLM_MODEL,
                prompt=prompt,
                max_tokens=50,
                temperature=0.1
            )

            if response.status_code == 200:
                core_phrase = response.output.text.strip()
                logger.info(f"Extracted core phrase: {core_phrase}")
                return core_phrase
            else:
                logger.error(f"LLM API error: {response.message}")
                return query

        except Exception as e:
            logger.error(f"Failed to extract core entities: {e}")
            return query


_destination_extractor = None


def get_destination_extractor() -> DestinationExtractorService:
    """Get singleton destination extractor instance"""
    global _destination_extractor
    if _destination_extractor is None:
        _destination_extractor = DestinationExtractorService()
    return _destination_extractor
