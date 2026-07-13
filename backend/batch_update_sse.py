"""
批量修改脚本：将所有document_processing和ai_recommend节点更新为使用统一的sse_utils
"""
import os
import re

# 定义需要修改的文件
document_nodes = [
    "E:\\大模型开发\\代码\\网站\\travel_proj\\backend\\app\\workflows\\document_processing\\nodes\\node_entity_extraction.py",
    "E:\\大模型开发\\代码\\网站\\travel_proj\\backend\\app\\workflows\\document_processing\\nodes\\node_rag_vectorization.py",
    "E:\\大模型开发\\代码\\网站\\travel_proj\\backend\\app\\workflows\\document_processing\\nodes\\node_graphrag_vectorization.py",
    "E:\\大模型开发\\代码\\网站\\travel_proj\\backend\\app\\workflows\\document_processing\\nodes\\node_finalize.py",
]

ai_recommend_nodes = [
    "E:\\大模型开发\\代码\\网站\\travel_proj\\backend\\app\\workflows\\ai_recommend\\nodes\\node_query_rewriter.py",
    "E:\\大模型开发\\代码\\网站\\travel_proj\\backend\\app\\workflows\\ai_recommend\\nodes\\node_parallel_retrieval.py",
    "E:\\大模型开发\\代码\\网站\\travel_proj\\backend\\app\\workflows\\ai_recommend\\nodes\\node_rrf_fusion.py",
    "E:\\大模型开发\\代码\\网站\\travel_proj\\backend\\app\\workflows\\ai_recommend\\nodes\\node_rerank.py",
    "E:\\大模型开发\\代码\\网站\\travel_proj\\backend\\app\\workflows\\ai_recommend\\nodes\\node_synthesizer.py",
]


def modify_document_node(file_path):
    """修改document_processing节点"""
    print(f"修改: {file_path}")

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. 替换导入
    content = re.sub(
        r'from \.\.utils import send_node_start, send_node_end',
        'from app.utils.sse_utils import send_node_start, send_node_end\n\nFLOW_TYPE = "document"',
        content
    )

    # 2. 替换send_node_start调用（添加flow_type参数）
    content = re.sub(
        r'await send_node_start\(\s*task_id=task_id,\s*step_id=',
        'await send_node_start(\n            task_id=task_id,\n            flow_type=FLOW_TYPE,\n            step_id=',
        content
    )

    # 3. 替换send_node_end调用（添加flow_type参数）
    content = re.sub(
        r'await send_node_end\(\s*task_id=task_id,\s*step_id=',
        'await send_node_end(\n            task_id=task_id,\n            flow_type=FLOW_TYPE,\n            step_id=',
        content
    )

    # 4. 移除多余的from ..utils导入
    content = re.sub(
        r'\s*from \.\.utils import send_node_start\s*',
        '',
        content
    )
    content = re.sub(
        r'\s*from \.\.utils import send_node_end\s*',
        '',
        content
    )

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"✓ 完成: {file_path}")


def modify_ai_recommend_node(file_path):
    """修改ai_recommend节点 - 添加SSE事件"""
    print(f"修改: {file_path}")

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 检查是否已经有导入
    if 'from app.utils.sse_utils import' not in content:
        # 在第一个from loguru之后添加导入
        content = re.sub(
            r'(from loguru import logger)',
            r'\1\nfrom app.utils.sse_utils import send_node_start, send_node_end\n\nFLOW_TYPE = "ai_recommend"',
            content,
            count=1
        )

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"✓ 完成: {file_path}")


if __name__ == "__main__":
    print("=" * 60)
    print("开始批量修改节点文件")
    print("=" * 60)

    print("\n修改document_processing节点...")
    for file_path in document_nodes:
        if os.path.exists(file_path):
            modify_document_node(file_path)
        else:
            print(f"✗ 文件不存在: {file_path}")

    print("\n修改ai_recommend节点...")
    for file_path in ai_recommend_nodes:
        if os.path.exists(file_path):
            modify_ai_recommend_node(file_path)
        else:
            print(f"✗ 文件不存在: {file_path}")

    print("\n" + "=" * 60)
    print("批量修改完成！")
    print("=" * 60)

    # 提示删除旧的utils.py
    utils_path = "E:\\大模型开发\\代码\\网站\\travel_proj\\backend\\app\\workflows\\document_processing\\utils.py"
    if os.path.exists(utils_path):
        print(f"\n⚠️  请手动删除旧文件: {utils_path}")

    print("\n下一步:")
    print("1. 检查修改后的文件")
    print("2. 删除 document_processing/utils.py")
    print("3. 重启后端测试")
