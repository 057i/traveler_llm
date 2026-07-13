"""
文本清洗工具 - 用于RAG索引前的文本预处理
"""
import re
from typing import Optional


def clean_text_for_rag(text: str) -> str:
    """
    清洗文本用于RAG索引

    处理内容:
    - 移除多余换行符
    - 移除多余空格
    - 移除特殊字符
    - 统一标点符号
    - 保留有意义的内容

    Args:
        text: 原始文本

    Returns:
        清洗后的文本
    """
    if not text:
        return ""

    # 1. 移除Windows和Unix换行符，替换为空格
    text = text.replace('\r\n', ' ')
    text = text.replace('\n', ' ')
    text = text.replace('\r', ' ')

    # 2. 移除制表符
    text = text.replace('\t', ' ')

    # 3. 移除零宽字符和不可见字符
    text = re.sub(r'[​-‏‪-‮﻿]', '', text)

    # 4. 移除多余空格（连续多个空格变为一个）
    text = re.sub(r'\s+', ' ', text)

    # 5. 移除字符串开头和结尾的空格
    text = text.strip()

    # 6. 统一中文标点符号
    text = text.replace('，', ', ')
    text = text.replace('。', '. ')
    text = text.replace('！', '! ')
    text = text.replace('？', '? ')
    text = text.replace('；', '; ')
    text = text.replace('：', ': ')
    text = text.replace('（', '(')
    text = text.replace('）', ')')
    text = text.replace('【', '[')
    text = text.replace('】', ']')
    text = text.replace('《', '<')
    text = text.replace('》', '>')
    text = text.replace('"', '"')
    text = text.replace('"', '"')
    text = text.replace(''', "'")
    text = text.replace(''', "'")

    # 7. 移除连续的标点符号（保留一个）
    text = re.sub(r'([.,!?;:])\1+', r'\1', text)

    # 8. 移除Markdown图片标记
    text = re.sub(r'!\[.*?\]\(.*?\)', '', text)

    # 9. 移除Markdown链接，保留链接文本
    text = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', text)

    # 10. 移除HTML标签
    text = re.sub(r'<[^>]+>', '', text)

    # 11. 移除特殊符号（保留基本标点和中英文）
    # 保留: 字母、数字、中文、基本标点、空格
    text = re.sub(r'[^\w\s.,!?;:()\[\]<>"\'-—·、。，！？；：（）【】《》""''·一-鿿]', ' ', text)

    # 12. 再次移除多余空格
    text = re.sub(r'\s+', ' ', text)

    # 13. 移除标点符号前的空格
    text = re.sub(r'\s+([.,!?;:])', r'\1', text)

    # 14. 确保标点符号后有空格（除非是字符串结尾）
    text = re.sub(r'([.,!?;:])(?=[^\s])', r'\1 ', text)

    # 15. 最终trim
    text = text.strip()

    return text


def clean_description(description: str, max_length: Optional[int] = None) -> str:
    """
    清洗描述文本（更严格的清洗）

    Args:
        description: 描述文本
        max_length: 最大长度限制

    Returns:
        清洗后的描述
    """
    # 基本清洗
    text = clean_text_for_rag(description)

    # 移除常见的无用前缀
    prefixes_to_remove = [
        '简介:', '简介：',
        '描述:', '描述：',
        '介绍:', '介绍：',
        '概述:', '概述：',
    ]
    for prefix in prefixes_to_remove:
        if text.startswith(prefix):
            text = text[len(prefix):].strip()

    # 限制长度
    if max_length and len(text) > max_length:
        text = text[:max_length] + '...'

    return text


def clean_list_field(items: list) -> list:
    """
    清洗列表字段

    Args:
        items: 列表项

    Returns:
        清洗后的列表
    """
    if not items:
        return []

    cleaned = []
    for item in items:
        if isinstance(item, str):
            cleaned_item = clean_text_for_rag(item)
            if cleaned_item:  # 只保留非空项
                cleaned.append(cleaned_item)
        else:
            cleaned.append(item)

    return cleaned


def clean_destination_data(destination: dict) -> dict:
    """
    清洗景点数据

    Args:
        destination: 景点字典

    Returns:
        清洗后的景点字典
    """
    cleaned = destination.copy()

    # 清洗字符串字段
    string_fields = ['name', 'description', 'category', 'province', 'city',
                    'address', 'ticket_price', 'opening_hours', 'visit_duration']

    for field in string_fields:
        if field in cleaned and cleaned[field]:
            if field == 'description':
                cleaned[field] = clean_description(cleaned[field], max_length=500)
            else:
                cleaned[field] = clean_text_for_rag(str(cleaned[field]))

    # 清洗列表字段
    list_fields = ['tags', 'best_season', 'suitable_for', 'features', 'budget_range']

    for field in list_fields:
        if field in cleaned and cleaned[field]:
            cleaned[field] = clean_list_field(cleaned[field])

    return cleaned


# ==================== 使用示例 ====================

if __name__ == "__main__":
    # 测试1: 基本清洗
    dirty_text = """
    三清山位于\n\n中国江西省\r\n上饶市。


    它是一座道教名山，　　拥有美丽的风景。！！
    """

    clean = clean_text_for_rag(dirty_text)
    print("清洗前:", repr(dirty_text))
    print("清洗后:", repr(clean))
    print()

    # 测试2: 清洗描述
    description = """
    简介：三清山位于\n江西省\n\n
    ![](image.jpg)
    [链接](http://example.com)

    它是一座道教名山。。。！！
    """

    clean_desc = clean_description(description)
    print("描述清洗前:", repr(description))
    print("描述清洗后:", repr(clean_desc))
    print()

    # 测试3: 清洗景点数据
    destination = {
        "name": "三清山\n\n",
        "description": "简介：三清山位于\n江西省\n\n上饶市。　　",
        "tags": ["道教名山\n", "  世界遗产  ", ""],
        "city": "上饶市　　",
    }

    cleaned_dest = clean_destination_data(destination)
    print("景点清洗前:", destination)
    print("景点清洗后:", cleaned_dest)
