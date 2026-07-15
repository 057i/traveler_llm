"""
文本清洗工具

用于清洗和标准化从文档中提取的景点数据
"""
from loguru import logger
import re


def clean_text_for_rag(text: str) -> str:
    """
    清洗文本用于RAG向量化

    功能：
    - 去除多余的空格和换行符
    - 去除特殊字符
    - 标准化文本格式

    Args:
        text: 原始文本

    Returns:
        str: 清洗后的文本
    """
    if not text or not isinstance(text, str):
        return ""

    try:
        # 去除多余的空白字符
        text = ' '.join(text.split())

        # 去除特殊控制字符
        text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)

        # 标准化标点符号
        text = text.replace('　', ' ')  # 全角空格

        return text.strip()

    except Exception as e:
        logger.warning(f"[TextCleaner] 清洗文本失败: {e}")
        return text


def clean_destination_data(destination: dict) -> dict:
    """
    清洗景点数据

    功能：
    - 去除多余的空格和换行符
    - 标准化字段名称
    - 验证必填字段

    Args:
        destination: 原始景点数据字典

    Returns:
        dict: 清洗后的景点数据
    """
    try:
        cleaned = {}

        # 清洗名称
        if 'name' in destination:
            cleaned['name'] = str(destination['name']).strip()

        # 清洗描述
        if 'description' in destination:
            desc = str(destination['description']).strip()
            # 移除多余的空格和换行符
            desc = ' '.join(desc.split())
            cleaned['description'] = desc

        # 清洗省份
        if 'province' in destination:
            cleaned['province'] = str(destination['province']).strip()

        # 清洗城市
        if 'city' in destination:
            cleaned['city'] = str(destination['city']).strip()

        # 清洗类型
        if 'type' in destination:
            cleaned['type'] = str(destination['type']).strip()
        elif 'category' in destination:
            cleaned['type'] = str(destination['category']).strip()

        # 清洗标签
        if 'tags' in destination and isinstance(destination['tags'], list):
            cleaned['tags'] = [str(tag).strip() for tag in destination['tags'] if tag]

        # 保留其他字段
        for key, value in destination.items():
            if key not in cleaned and value is not None:
                if isinstance(value, str):
                    cleaned[key] = value.strip()
                else:
                    cleaned[key] = value

        return cleaned

    except Exception as e:
        logger.warning(f"[TextCleaner] 清洗数据失败: {e}，返回原数据")
        return destination
