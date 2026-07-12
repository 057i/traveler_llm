"""
Batch fix encoding issues in core directory
"""
from pathlib import Path
import re

def has_garbled(text):
    """Check if text contains garbled characters"""
    garbled_chars = '閸閺閻閼閽閾闂闁铏鈧鈩鈪濞濡濠濢濣濤濥瀵鎮鎯鎰鎱鎲鎳鎴鎵缁缂缃缄缅缆缇缈'
    return any(c in text for c in garbled_chars)

def clean_file(filepath):
    """Clean a single Python file"""
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()

    cleaned_lines = []
    in_docstring = False
    docstring_marker = None

    for i, line in enumerate(lines):
        stripped = line.strip()

        # Handle docstrings (module, class, function)
        if '"""' in line or "'''" in line:
            marker = '"""' if '"""' in line else "'''"
            count = line.count(marker)

            if count == 2:
                # Single-line docstring
                if has_garbled(line):
                    continue  # Skip garbled single-line docstring
                else:
                    cleaned_lines.append(line)
            elif count == 1:
                if not in_docstring:
                    # Docstring start
                    if has_garbled(line):
                        in_docstring = True
                        docstring_marker = marker
                        continue  # Skip this line and start skipping
                    else:
                        in_docstring = True
                        docstring_marker = marker
                        cleaned_lines.append(line)
                else:
                    # Docstring end
                    if has_garbled(line):
                        in_docstring = False
                        docstring_marker = None
                        continue  # Skip closing line
                    else:
                        in_docstring = False
                        docstring_marker = None
                        cleaned_lines.append(line)
            continue

        # Skip lines inside garbled docstring
        if in_docstring and docstring_marker:
            # Check if we should skip this docstring
            if i > 0 and has_garbled(lines[i-1]):
                continue
            cleaned_lines.append(line)
            continue

        # Handle comment lines
        if stripped.startswith('#'):
            if has_garbled(line):
                continue  # Skip garbled comment
            else:
                cleaned_lines.append(line)
            continue

        # Handle inline comments
        if '#' in line:
            parts = line.split('#', 1)
            code_part = parts[0]
            comment_part = parts[1] if len(parts) > 1 else ''

            if has_garbled(comment_part):
                # Remove comment, keep code
                cleaned_lines.append(code_part.rstrip() + '\n')
            else:
                cleaned_lines.append(line)
            continue

        # Handle logger statements with garbled strings
        if 'logger.' in line and has_garbled(line):
            indent = len(line) - len(line.lstrip())
            method = 'info'
            if 'logger.error' in line:
                method = 'error'
                if '{e}' in line or '{str(e)}' in line:
                    cleaned_lines.append(' ' * indent + f'logger.{method}(f"Error: {{e}}")\n')
                else:
                    cleaned_lines.append(' ' * indent + f'logger.{method}("Error occurred")\n')
            elif 'logger.warning' in line:
                method = 'warning'
                cleaned_lines.append(' ' * indent + f'logger.{method}("Warning")\n')
            elif 'logger.success' in line:
                method = 'success'
                cleaned_lines.append(' ' * indent + f'logger.{method}("Success")\n')
            elif 'logger.info' in line:
                cleaned_lines.append(' ' * indent + 'logger.info("Processing")\n')
            else:
                cleaned_lines.append(line)
            continue

        # Keep regular code lines
        cleaned_lines.append(line)

    # Write back
    with open(filepath, 'w', encoding='utf-8', newline='\n') as f:
        f.writelines(cleaned_lines)

    return True

# Process all Python files in core directory
core_dir = Path('app/core')
py_files = [f for f in core_dir.glob('*.py') if f.name != '__pycache__']

print(f"Found {len(py_files)} Python files in core directory\n")

cleaned_count = 0
for filepath in py_files:
    try:
        clean_file(filepath)
        print(f"Cleaned: {filepath.name}")
        cleaned_count += 1
    except Exception as e:
        print(f"Error cleaning {filepath.name}: {e}")

print(f"\nTotal cleaned: {cleaned_count}/{len(py_files)} files")
