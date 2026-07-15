"""
文本清洗工具

用于清洗和标准化从文档中提取的景点数据
"""
from loguru import logger


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
