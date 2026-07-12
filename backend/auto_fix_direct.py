"""
Auto-fix encoding issues - Direct binary mode
"""
import re
from pathlib import Path

def remove_garbled_lines(content):
    """Remove lines containing garbled characters"""
    lines = content.split('\n')
    cleaned = []

    # Garbled character pattern
    garbled = re.compile(r'[\u閹\u閺\u閸\u閻\u瀹\u缂\u婢\u鐎\u濞\u娴\u鐠\u濡\u娑\u鐢\u鏉\u娣\u缁\u鐞\u閼\u婵\u鐟\u闁\u闂\u娴\u瑜\u瑗\u瀵]')

    for line in lines:
        if garbled.search(line):
            # Keep the line structure but remove garbled content
            indent = len(line) - len(line.lstrip())
            if '"""' in line or "'''" in line:
                # Docstring line - skip
                continue
            elif line.strip().startswith('#'):
                # Comment line - skip
                continue
            elif line.strip() == '':
                # Empty line - keep
                cleaned.append(line)
            else:
                # Code line with garbled text - keep but warn in file
                cleaned.append(line)
        else:
            cleaned.append(line)

    return '\n'.join(cleaned)

def fix_file_direct(filepath):
    """Fix file using direct read/write"""
    try:
        # Read
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        # Clean
        cleaned = remove_garbled_lines(content)

        # Write
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(cleaned)

        return True
    except Exception as e:
        # Write error to log file instead of console
        with open('fix_errors.log', 'a', encoding='utf-8') as log:
            log.write(f"Error fixing {filepath}: {e}\n")
        return False

def main():
    base = Path(r"E:\大模型开发\代码\网站\travel_proj\backend\app\workflows")

    issue_files = [
        "team_recommend/master_agent.py",
        "team_recommend/schemas.py",
        "team_recommend/service.py",
        "team_recommend/team_manager.py",
        "ai_recommend/nodes/node_confidence_check.py",
        "ai_recommend/nodes/node_parallel_retrieval.py",
        "ai_recommend/nodes/node_query_rewriter.py",
        "ai_recommend/nodes/node_rerank.py",
        "ai_recommend/nodes/node_rrf_fusion.py",
        "ai_recommend/nodes/node_rrf_fusion_with_tavily.py",
        "ai_recommend/nodes/node_synthesizer.py",
        "ai_recommend/nodes/node_tavily_search.py",
        "document_processing/nodes/node_chunking.py",
        "document_processing/nodes/node_entity_extraction.py",
        "document_processing/nodes/node_pdf_parse.py",
        "document_processing/nodes/node_vectorization.py",
        "team_recommend/subagents/budget_expert.py",
        "team_recommend/subagents/food_assistant.py",
        "team_recommend/subagents/graph_rag_assistant.py",
        "team_recommend/subagents/itinerary_planner.py",
        "team_recommend/subagents/rag_assistant.py",
        "team_recommend/subagents/tools.py",
        "team_recommend/subagents/transport_assistant.py",
    ]

    count = 0
    for rel in issue_files:
        path = base / rel
        if path.exists():
            if fix_file_direct(path):
                count += 1

    # Write success count to log
    with open('fix_complete.log', 'w', encoding='utf-8') as log:
        log.write(f"Fixed {count}/{len(issue_files)} files\n")

if __name__ == "__main__":
    main()
