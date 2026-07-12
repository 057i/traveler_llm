"""Fix all core files with syntax errors"""
from pathlib import Path

def fix_docstring(filepath):
    """Fix unclosed docstring at the beginning of file"""
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    if not lines:
        return False

    # Check if first line is unclosed docstring
    if lines[0].strip() == '"""':
        # Replace with closed docstring
        lines[0] = '"""Module"""\n'

        with open(filepath, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        return True

    return False

# Fix all problem files
files = [
    'integrated_search_client.py',
    'milvus_client.py',
    'neo4j_graph_client.py',
    'reranker.py',
    'rerank_client.py',
    'tavily_client.py',
    'workflow_engine.py'
]

core_dir = Path('app/core')
fixed = 0

for filename in files:
    filepath = core_dir / filename
    if filepath.exists():
        if fix_docstring(filepath):
            print(f'Fixed: {filename}')
            fixed += 1
        else:
            print(f'Skipped: {filename}')

print(f'\nTotal fixed: {fixed} files')
