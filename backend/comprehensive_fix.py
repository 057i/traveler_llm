"""
Comprehensive fix for workflows encoding issues
Remove all garbled Chinese and malformed UTF-8 characters
"""
import re
from pathlib import Path

def is_garbled_line(line):
    """Check if a line contains garbled characters"""
    # Common garbled character ranges
    garbled_pattern = re.compile(
        r'[鑹钉针钇锡\u7f钗钅钗鑾'
        r'鑰鑳镑镘镦钗钗钇\u7f钗'
        r'钉钉锡钆针鑰钗钇鑰]'
    )

    # Also check for specific garbled sequences
    if any(bad in line for bad in ['閹', '閺', '閸', '閻', '瀹', '缂', '婢', '鐎', '濞',
                                     '娴', '鐠', '濡', '娑', '鐢', '鏉', '娣', '缁', '鐞',
                                     '閼', '婵', '鐟', '闁', '闂', '瑜', '瑗', '瀵']):
        return True

    return bool(garbled_pattern.search(line))

def clean_content(content):
    """Remove garbled lines from content"""
    lines = content.split('\n')
    cleaned_lines = []
    skip_next = False

    for i, line in enumerate(lines):
        stripped = line.strip()

        # Skip empty lines - keep them
        if not stripped:
            cleaned_lines.append(line)
            continue

        # Check if line contains garbled text
        if is_garbled_line(line):
            # Skip garbled docstrings and comments
            if stripped.startswith('"""') or stripped.startswith("'''"):
                skip_next = True
                continue
            elif stripped.startswith('#'):
                continue
            elif '"""' in line or "'''" in line:
                continue
            # Keep code lines but they may need manual fixing

        cleaned_lines.append(line)

    return '\n'.join(cleaned_lines)

def fix_file(filepath):
    """Fix encoding in a single file"""
    try:
        # Read with UTF-8, ignoring errors
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            original = f.read()

        # Clean
        cleaned = clean_content(original)

        # Only write if changed
        if cleaned != original:
            with open(filepath, 'w', encoding='utf-8', newline='\n') as f:
                f.write(cleaned)
            return True, "modified"
        return True, "no_change"

    except Exception as e:
        return False, str(e)

def main():
    base = Path(r"E:\大模型开发\代码\网站\travel_proj\backend\app\workflows")

    files_to_fix = [
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

    results = []
    for rel_path in files_to_fix:
        filepath = base / rel_path
        if filepath.exists():
            success, status = fix_file(filepath)
            results.append((rel_path, success, status))

    # Write results to log
    with open('fix_results.txt', 'w', encoding='utf-8') as log:
        log.write("Fix Results:\n")
        log.write("=" * 80 + "\n")

        modified = sum(1 for _, s, st in results if s and st == "modified")
        unchanged = sum(1 for _, s, st in results if s and st == "no_change")
        failed = sum(1 for _, s, _ in results if not s)

        log.write(f"Modified: {modified}\n")
        log.write(f"Unchanged: {unchanged}\n")
        log.write(f"Failed: {failed}\n")
        log.write(f"Total: {len(results)}\n\n")

        for path, success, status in results:
            log.write(f"{'[OK]' if success else '[FAIL]'} {path}: {status}\n")

if __name__ == "__main__":
    main()
