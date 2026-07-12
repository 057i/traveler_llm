from pathlib import Path
import re

target_files = [
    "app/core/fusion_strategies.py",
    "app/core/health_check.py",
    "app/core/integrated_search_client.py",
    "app/core/milvus_client.py",
    "app/core/neo4j_graph_client.py",
    "app/core/reranker.py",
    "app/core/rerank_client.py",
    "app/core/workflow_engine.py",
]

def is_valid_char(char):
    """判断字符是否有效"""
    code = ord(char)
    # ASCII可打印字符
    if 32 <= code <= 126:
        return True
    # 常见中文范围
    if 0x4E00 <= code <= 0x9FFF:
        return True
    # 换行、制表符等
    if char in '\n\r\t':
        return True
    return False

fixed_count = 0
for filepath in target_files:
    p = Path(filepath)
    if not p.exists():
        continue

    with open(p, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    # 过滤无效字符
    cleaned = ""
    for c in content:
        if is_valid_char(c):
            cleaned += c

    # 清理多余的空行
    lines = cleaned.split("\n")
    cleaned_lines = []
    prev_empty = False
    for line in lines:
        if line.strip():
            cleaned_lines.append(line)
            prev_empty = False
        elif not prev_empty:
            cleaned_lines.append(line)
            prev_empty = True

    cleaned = "\n".join(cleaned_lines)

    if cleaned != content:
        with open(p, "w", encoding="utf-8", newline="\n") as f:
            f.write(cleaned)
        print(f"Cleaned: {p.name}")
        fixed_count += 1
    else:
        print(f"No change: {p.name}")

print(f"\nTotal cleaned: {fixed_count} files")
