"""
Fix encoding issues in workflows directory
Remove Chinese and garbled comments
"""
import os
import re
from pathlib import Path

def has_encoding_issues(content):
    """Check if content has encoding issues"""
    garbled_patterns = [
        r'閹|閺|閸|閻|瀹|缂|婢|鐎|濞|娴|鐠|濡|娑|鐢',  # Common garbled characters
    ]

    for pattern in garbled_patterns:
        if re.search(pattern, content):
            return True
    return False

def scan_directory(base_path):
    """Scan directory for files with encoding issues"""
    base_path = Path(base_path)
    issues = []

    for py_file in base_path.rglob("*.py"):
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()

            if has_encoding_issues(content):
                issues.append(str(py_file))
                print(f"[ISSUE] {py_file.relative_to(base_path)}")
            else:
                print(f"[OK] {py_file.relative_to(base_path)}")

        except Exception as e:
            print(f"[ERROR] {py_file.relative_to(base_path)}: {e}")

    return issues

if __name__ == "__main__":
    workflows_path = r"E:\大模型开发\代码\网站\travel_proj\backend\app\workflows"

    print("=" * 80)
    print("Scanning workflows directory for encoding issues...")
    print("=" * 80)

    issues = scan_directory(workflows_path)

    print("\n" + "=" * 80)
    print(f"Found {len(issues)} files with encoding issues:")
    print("=" * 80)

    for file in issues:
        print(f"  - {file}")
