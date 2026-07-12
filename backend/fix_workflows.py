"""
Batch fix workflows files - remove garbled Chinese characters
"""
from pathlib import Path
import re


def is_garbled(char):
    """Check if character is garbled"""
    code = ord(char)
    # Common garbled character ranges
    if code > 127:
        garbled_chars = [
            '閹', '閺', '閻', '閼', '閽', '閾', '閿', '鐎', '鐏', '鐐',
            '瀹', '儰', '缍', '斿', '浣', '哥', '穿', '垮', '函', '绱',
            '欓', '崗', '鐓', '庮', '啇', '炲', '偊', '婢', '跺', '嫮',
            '婇', '弬', '鍥', '傞', '惃', '鍕', '瘜', '忋', '儱', '褰',
            '娴', '犺', '濮', '烮', '傚', '洣', '娆', '崥', '崘', '鍛',
            '涘', '牆', '鐡', '懞', '鍌', '礆', '鎮', '婄', '紒', '鎾',
            '寸', '亯', '涙', '鍚', '锛', '灏', '斂', '娓', '瀹', '瓑',
        ]
        return char in garbled_chars
    return False


def clean_line(line):
    """Clean a single line"""
    # Remove lines that are purely garbled or comments with garbled text
    stripped = line.strip()

    # Check if line is a comment with garbled text
    if stripped.startswith('#'):
        has_garbled = any(is_garbled(c) for c in line)
        if has_garbled:
            return None  # Remove this line

    # Check if line is in a string literal with garbled text
    if any(is_garbled(c) for c in line):
        # Try to replace garbled parts in string literals
        if '"' in line or "'" in line:
            # String literal - replace with placeholder
            if 'state["answer"]' in line or 'state["intent"]' in line:
                # Replace garbled string with English
                if 'state["answer"]' in line:
                    indent = len(line) - len(line.lstrip())
                    return ' ' * indent + 'state["answer"] = "Sorry, I cannot generate an answer."\n'
                elif 'state["intent"]' in line:
                    return None  # Will be handled by keyword matching

            # For other string literals, try to clean
            cleaned = ''
            in_string = False
            string_char = None

            for i, char in enumerate(line):
                if char in ['"', "'"] and (i == 0 or line[i-1] != '\\'):
                    if not in_string:
                        in_string = True
                        string_char = char
                        cleaned += char
                    elif char == string_char:
                        in_string = False
                        string_char = None
                        cleaned += char
                    else:
                        cleaned += char
                elif in_string and is_garbled(char):
                    # Skip garbled character in string
                    continue
                else:
                    cleaned += char

            return cleaned

    return line


def fix_file(filepath):
    """Fix a single file"""
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()

        fixed_lines = []
        in_docstring = False
        skip_docstring = False

        for i, line in enumerate(lines):
            # Handle docstrings
            if '"""' in line or "'''" in line:
                marker = '"""' if '"""' in line else "'''"

                if not in_docstring:
                    # Opening docstring
                    has_garbled = any(is_garbled(c) for c in line)
                    if has_garbled:
                        # Skip garbled docstring
                        in_docstring = True
                        skip_docstring = True
                        if line.count(marker) == 2:
                            # Single-line docstring
                            in_docstring = False
                            skip_docstring = False
                        continue
                    else:
                        fixed_lines.append(line)
                        if line.count(marker) == 2:
                            in_docstring = False
                        else:
                            in_docstring = True
                        continue
                else:
                    # Closing docstring
                    in_docstring = False
                    if not skip_docstring:
                        fixed_lines.append(line)
                    skip_docstring = False
                    continue

            if in_docstring:
                if not skip_docstring:
                    fixed_lines.append(line)
                continue

            # Clean regular lines
            cleaned = clean_line(line)
            if cleaned is not None:
                fixed_lines.append(cleaned)

        # Write back
        with open(filepath, 'w', encoding='utf-8') as f:
            f.writelines(fixed_lines)

        return True

    except Exception as e:
        print(f"Error fixing {filepath}: {e}")
        return False


def main():
    """Main function"""
    workflows_dir = Path('app/workflows')

    error_files = [
        'chat_workflow.py',
        'manager.py',
        'websocket_workflow.py',
        'ai_recommend/graph_builder.py',
        'ai_recommend/service.py',
        'ai_recommend/state.py',
        'ai_recommend/nodes/node_confidence_check.py',
        'ai_recommend/nodes/node_parallel_retrieval.py',
        'ai_recommend/nodes/node_query_rewriter.py',
        'ai_recommend/nodes/node_rerank.py',
        'ai_recommend/nodes/node_rrf_fusion.py',
        'ai_recommend/nodes/node_rrf_fusion_with_tavily.py',
        'ai_recommend/nodes/node_synthesizer.py',
        'ai_recommend/nodes/node_tavily_search.py',
        'document_processing/graph_builder.py',
        'document_processing/state.py',
        'document_processing/nodes/node_chunking.py',
        'document_processing/nodes/node_entity_extraction.py',
        'document_processing/nodes/node_pdf_parse.py',
        'document_processing/nodes/node_vectorization.py',
        'team_recommend/master_agent.py',
        'team_recommend/schemas.py',
        'team_recommend/service.py',
        'team_recommend/team_manager.py',
        'team_recommend/subagents/base.py',
        'team_recommend/subagents/budget_expert.py',
        'team_recommend/subagents/food_assistant.py',
        'team_recommend/subagents/graph_rag_assistant.py',
        'team_recommend/subagents/itinerary_planner.py',
        'team_recommend/subagents/rag_assistant.py',
        'team_recommend/subagents/tools.py',
        'team_recommend/subagents/transport_assistant.py',
    ]

    fixed_count = 0
    for file in error_files:
        filepath = workflows_dir / file
        if filepath.exists():
            if fix_file(filepath):
                fixed_count += 1
                print(f"Fixed: {file}")
            else:
                print(f"Failed: {file}")
        else:
            print(f"Not found: {file}")

    print(f"\nFixed {fixed_count}/{len(error_files)} files")


if __name__ == '__main__':
    main()
