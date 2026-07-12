"""
Node: Entity Extraction with Qwen

Extract destination entities from text chunks using Qwen LLM
"""
from loguru import logger
from ..state import DocumentProcessingState, Destination
from typing import List, Dict, Any
import json


async def extract_entities(state: DocumentProcessingState) -> DocumentProcessingState:
    """
    Step 4: Extract destination entities using Qwen LLM

    Processes chunks and extracts structured destination data
    """
    task_id = state.get('task_id')

    # 发送 node_start 事件
    if task_id:
        from ..utils import send_node_start
        await send_node_start(
            task_id=task_id,
            step_id="extract",
            step_name="实体提取",
            progress=60,
            message="正在使用Qwen提取景点实体..."
        )

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

        all_destinations: List[Destination] = []

        # Process each chunk (串行处理)
        for i, chunk in enumerate(chunks[:10]):  # Limit to 10 chunks for testing
            logger.info(f"[Extract] Processing chunk {i+1}/{min(len(chunks), 10)}")

            prompt = f"""你是专业的旅游景点信息提取助手。从文本中提取景点信息并返回JSON数组。

文本：
{chunk[:2000]}

输出格式要求：
1. 必须返回标准JSON数组格式
2. 从 [ 开始，到 ] 结束
3. 多个景点用逗号分隔
4. 不要添加任何解释文字
5. 不要使用markdown代码块
6. 确保JSON语法完全正确（注意逗号、引号、括号）

JSON数组示例（严格参照此格式）：
[
  {{
    "name": "景点名称",
    "city": "城市",
    "province": "省份",
    "type": "Attraction",
    "description": "简短描述",
    "tags": ["标签1", "标签2"],
    "best_season": ["春季"],
    "budget_range": [100, 200],
    "suitable_for": ["家庭"],
    "features": ["特色1"],
    "rating": 4.5,
    "category": "山脉",
    "address": "地址",
    "opening_hours": "全天",
    "ticket_price": "免费",
    "visit_duration": "2小时"
  }},
  {{
    "name": "景点2",
    "city": "城市2",
    "province": "省份2"
  }}
]

关键规则：
- 数组中每个对象之间用逗号分隔
- 对象内每个字段之间用逗号分隔
- 字符串必须用双引号
- 数字不要用引号
- 如果没有景点，返回：[]
- 直接返回JSON，不要其他内容

现在提取："""

            try:
                response = Generation.call(
                    model=settings.QWEN_MODEL,
                    prompt=prompt,
                    api_key=settings.DASHSCOPE_API_KEY,
                    temperature=0.01,
                    top_p=0.5
                )

                if response.status_code == 200:
                    result_text = response.output.text.strip()
                    result_text = result_text.replace('```json', '').replace('```', '').strip()

                    try:
                        destinations = json.loads(result_text)

                        if isinstance(destinations, list):
                            for dest in destinations:
                                if isinstance(dest, dict) and dest.get('name'):
                                    logger.info(
                                        f"[Extract] 实体: {dest.get('name', 'Unknown')} | "
                                        f"省份: {dest.get('province', '未识别')} | "
                                        f"城市: {dest.get('city', '未识别')} | "
                                        f"类型: {dest.get('type', 'Unknown')}"
                                    )

                                    destination: Destination = {
                                        'name': dest.get('name', ''),
                                        'city': dest.get('city', ''),
                                        'province': dest.get('province', ''),
                                        'type': dest.get('type', 'Attraction'),
                                        'description': dest.get('description', ''),
                                        'tags': dest.get('tags', []),
                                        'best_season': dest.get('best_season', []),
                                        'budget_range': dest.get('budget_range', [0, 0]),
                                        'suitable_for': dest.get('suitable_for', []),
                                        'features': dest.get('features', []),
                                        'rating': float(dest.get('rating', 4.0)),
                                        'image_url': dest.get('image_url', ''),
                                        'graph_id': dest.get('graph_id', f"{dest.get('name', '')}_未知"),
                                        'category': dest.get('category', ''),
                                        'address': dest.get('address', ''),
                                        'opening_hours': dest.get('opening_hours', '全天'),
                                        'ticket_price': dest.get('ticket_price', ''),
                                        'visit_duration': dest.get('visit_duration', '')
                                    }
                                    all_destinations.append(destination)

                        logger.success(f"[Extract] Chunk {i+1}: extracted {len(destinations)} destinations")

                    except json.JSONDecodeError as json_err:
                        logger.warning(f"[Extract] JSON parse failed for chunk {i+1}: {json_err}")
                        continue

            except Exception as api_err:
                logger.warning(f"[Extract] API call failed for chunk {i+1}: {api_err}")
                continue

        state['destinations'] = all_destinations
        state['extract_success'] = True

        logger.success(f"[Extract] Total extracted: {len(all_destinations)} destinations")

        # Save to Neo4j (GraphRAG)
        if all_destinations:
            try:
                logger.info("[Extract] Saving to Neo4j...")
                from app.core.neo4j_client import get_neo4j_client

                neo4j = get_neo4j_client()

                for dest in all_destinations:
                    neo4j.create_destination(
                        name=dest['name'],
                        description=dest['description'],
                        location=f"{dest.get('province', '')}{dest.get('city', '')}",
                        properties=dest
                    )

                logger.success(f"[Extract] Saved {len(all_destinations)} destinations to Neo4j")

            except Exception as neo4j_error:
                logger.error(f"[Extract] Failed to save to Neo4j: {neo4j_error}")

        # 发送 node_end 事件
        if task_id:
            from ..utils import send_node_end
            await send_node_end(
                task_id=task_id,
                step_id="extract",
                step_name="实体提取",
                progress=60,
                message=f"实体提取完成 ({len(all_destinations)} 个景点)"
            )

    except Exception as e:
        logger.error(f"[Extract] Extraction failed: {e}")
        import traceback
        traceback.print_exc()
        state['destinations'] = []
        state['extract_success'] = False
        state.setdefault('errors', []).append(f"Extraction error: {str(e)}")

    return state


async def extract_fallback(state: DocumentProcessingState) -> DocumentProcessingState:
    """
    Fallback: Skip entity extraction
    """
    logger.warning("[Extract] Using fallback - skipping entity extraction")
    state['destinations'] = []
    state['extract_success'] = True
    return state
