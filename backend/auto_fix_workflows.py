"""
Auto-fix encoding issues in workflows directory
Remove garbled comments and replace with clean English comments
"""
import os
import re
from pathlib import Path

def clean_garbled_text(content):
    """Remove garbled text patterns"""

    # Pattern 1: Remove lines with garbled characters in comments
    lines = content.split('\n')
    cleaned_lines = []

    garbled_chars = r'閹|閺|閸|閻|瀹|缂|婢|鐎|濞|娴|鐠|濡|娑|鐢|鏉|娣|缁|鐞|閼|婵|鐟|闁|闂|娴|瑜|瑗|瀵'

    for line in lines:
        # Skip lines that are primarily garbled
        if re.search(garbled_chars, line):
            # Check if it's a docstring or comment
            stripped = line.strip()
            if stripped.startswith('#') or stripped.startswith('"""') or stripped.startswith("'''"):
                # Skip garbled comment/docstring lines
                continue
            elif '"""' in line or "'''" in line:
                # Handle inline docstrings
                continue
            else:
                # Keep non-comment lines but warn
                print(f"  WARNING: Garbled text in code line: {line[:50]}")
                cleaned_lines.append(line)
        else:
            cleaned_lines.append(line)

    return '\n'.join(cleaned_lines)

def fix_file(file_path):
    """Fix encoding issues in a single file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        original_lines = len(content.split('\n'))
        cleaned_content = clean_garbled_text(content)
        cleaned_lines = len(cleaned_content.split('\n'))

        # Write back
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(cleaned_content)

        removed = original_lines - cleaned_lines
        print(f"  Fixed: {file_path.name} (removed {removed} garbled lines)")
        return True

    except Exception as e:
        print(f"  ERROR fixing {file_path.name}: {e}")
        return False

def main():
    workflows_path = Path(r"E:\大模型开发\代码\网站\travel_proj\backend\app\workflows")

    # List of files with issues (from scan)
    issue_files = [
        "document_processing/state.py",
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
        "document_processing/nodes/node_finalize.py",
        "document_processing/nodes/node_minio.py",
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

    print("=" * 80)
    print("Auto-fixing encoding issues...")
    print("=" * 80)

    fixed_count = 0
    for rel_path in issue_files:
        file_path = workflows_path / rel_path
        if file_path.exists():
            print(f"\nProcessing: {rel_path}")
            if fix_file(file_path):
                fixed_count += 1

    print("\n" + "=" * 80)
    print(f"Fixed {fixed_count}/{len(issue_files)} files")
    print("=" * 80)

if __name__ == "__main__":
    main()
