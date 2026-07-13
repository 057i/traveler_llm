"""
Node: Entity Extraction with Qwen

Extract destination entities from text chunks using Qwen LLM
"""
from loguru import logger
from ..state import DocumentProcessingState, Destination
from typing import List, Dict, Any
import json
from app.utils.sse_utils import send_node_start, send_node_end

FLOW_TYPE = "document"


# ==================== 步骤函数 ====================

def step1_build_extraction_prompt(chunk: str) -> str:
    """
    Step 1: 构建实体提取的Prompt

    Args:
        chunk: 文本块

    Returns:
        构建好的prompt
    """
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

    return prompt


def step2_call_qwen_api(prompt: str) -> str:
    """
    Step 2: 调用Qwen API进行实体提取

    Args:
        prompt: 提取prompt

    Returns:
        API返回的文本结果
    """
    from dashscope import Generation
    from config.settings import settings

    response = Generation.call(
        model=settings.QWEN_MODEL,
        prompt=prompt,
        api_key=settings.DASHSCOPE_API_KEY,
        temperature=0.01,
        top_p=0.5
    )

    if response.status_code != 200:
        raise Exception(f"Qwen API failed: {response.status_code}")

    result_text = response.output.text.strip()
    result_text = result_text.replace('```json', '').replace('```', '').strip()

    return result_text


def step3_parse_and_validate(result_text: str, chunk_index: int) -> List[Destination]:
    """
    Step 3: 解析并验证提取结果

    Args:
        result_text: API返回的JSON文本
        chunk_index: 当前chunk索引

    Returns:
        景点实体列表
    """
    destinations = json.loads(result_text)
    validated_destinations = []

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
                validated_destinations.append(destination)

    logger.success(f"[Extract] Chunk {chunk_index}: extracted {len(validated_destinations)} destinations")
    return validated_destinations


def step4_save_to_neo4j(destinations: List[Destination]):
    """
    Step 4: 保存景点到Neo4j（可选）

    Args:
        destinations: 景点列表
    """
    from app.core.neo4j_client import get_neo4j_client

    logger.info("[Extract] Saving to Neo4j...")
    neo4j = get_neo4j_client()

    for dest in destinations:
        neo4j.create_destination(
            name=dest['name'],
            description=dest['description'],
            location=f"{dest.get('province', '')}{dest.get('city', '')}",
            properties=dest
        )

    logger.success(f"[Extract] Saved {len(destinations)} destinations to Neo4j")


# ==================== 主节点函数 ====================

async def extract_entities(state: DocumentProcessingState) -> DocumentProcessingState:
    """
    Node: 使用Qwen提取景点实体

    流程:
        1. 构建提取prompt
        2. 调用Qwen API
        3. 解析并验证结果
        4. 保存到Neo4j（可选）

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
            step_id="extract",
            step_name="实体提取",
            progress=60,
            message="正在使用Qwen提取景点实体..."
        )

    logger.info("[Extract] === Starting entity extraction ===")

    try:
        chunks = state.get('chunks', [])

        if not chunks:
            logger.warning("[Extract] No chunks to extract from")
            state['destinations'] = []
            state['extract_success'] = False
            return state

        all_destinations: List[Destination] = []

        # 处理每个chunk（限制前10个）
        for i, chunk in enumerate(chunks[:10], 1):
            logger.info(f"[Extract] Processing chunk {i}/{min(len(chunks), 10)}")

            try:
                # Step 1: 构建prompt
                prompt = step1_build_extraction_prompt(chunk)

                # Step 2: 调用Qwen API
                result_text = step2_call_qwen_api(prompt)

                # Step 3: 解析并验证
                chunk_destinations = step3_parse_and_validate(result_text, i)
                all_destinations.extend(chunk_destinations)

            except json.JSONDecodeError as json_err:
                logger.warning(f"[Extract] JSON parse failed for chunk {i}: {json_err}")
                continue

            except Exception as api_err:
                logger.warning(f"[Extract] API call failed for chunk {i}: {api_err}")
                continue

        # 清洗提取的数据
        logger.info(f"[Extract] 清洗 {len(all_destinations)} 个景点数据...")
        from app.utils.text_cleaner import clean_destination_data

        cleaned_destinations = []
        for dest in all_destinations:
            try:
                cleaned_dest = clean_destination_data(dest)
                cleaned_destinations.append(cleaned_dest)
            except Exception as e:
                logger.warning(f"[Extract] 清洗景点数据失败: {e}，保留原数据")
                cleaned_destinations.append(dest)

        logger.success(f"[Extract] 数据清洗完成")

        # 保存结果到state
        state['destinations'] = cleaned_destinations
        state['extract_success'] = True

        logger.success(f"[Extract] Total extracted: {len(cleaned_destinations)} destinations")

        # Step 4: 保存到Neo4j（可选）
        if cleaned_destinations:
            try:
                step4_save_to_neo4j(cleaned_destinations)
            except Exception as neo4j_error:
                logger.error(f"[Extract] Failed to save to Neo4j: {neo4j_error}")

        logger.success(f"[Extract] === Extraction completed: {len(cleaned_destinations)} destinations ===")

        # 发送node_end事件
        if task_id:
            await send_node_end(
                task_id=task_id,
                flow_type=FLOW_TYPE,
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
    Fallback: 跳过实体提取
    """
    logger.warning("[Extract] Using fallback - skipping entity extraction")
    state['destinations'] = []
    state['extract_success'] = True
    return state
