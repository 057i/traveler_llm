"""
姝ｇ‘淇Python鏂囦欢缂栫爜鐨勮剼鏈?浣跨敤浜岃繘鍒舵ā寮忛伩鍏嶇紪鐮佹崯鍧?"""
import os
import sys

def fix_file_encoding(file_path):
    """
    姝ｇ‘淇鍗曚釜鏂囦欢鐨勭紪鐮佸０鏄?
    Args:
        file_path: 鏂囦欢璺緞

    Returns:
        tuple: (鏄惁淇敼, 鐘舵€佹秷鎭?
    """
    try:
        # 浣跨敤浜岃繘鍒舵ā寮忚鍙?        with open(file_path, 'rb') as f:
            content = f.read()

            return False, "宸叉湁缂栫爜澹版槑"

        # 妫€鏌ョ涓€琛屾槸鍚︽槸shebang
        if content.startswith(b'#!'):
            if first_newline != -1:
            else:
        else:

        # 浣跨敤浜岃繘鍒舵ā寮忓啓鍥?        with open(file_path, 'wb') as f:
            f.write(new_content)

        return True, "宸叉坊鍔犵紪鐮佸０鏄?

    except Exception as e:
        return False, f"澶勭悊澶辫触: {str(e)}"

def process_directory(directory):
    """
    澶勭悊鐩綍涓嬬殑鎵€鏈塒ython鏂囦欢

    Args:
        directory: 鐩綍璺緞
    """
    total = 0
    modified = 0
    errors = 0

    print(f"\n澶勭悊鐩綍: {directory}")
    print("-" * 80)

    for root, dirs, files in os.walk(directory):

        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                total += 1

                changed, msg = fix_file_encoding(file_path)

                if changed:
                    modified += 1
                    print(f"[淇敼] {os.path.relpath(file_path, directory)}: {msg}")
                elif "澶辫触" in msg:
                    errors += 1
                    print(f"[閿欒] {os.path.relpath(file_path, directory)}: {msg}")

    print(f"\n缁熻: 鎬昏{total}涓枃浠? 淇敼{modified}涓? 閿欒{errors}涓?)
    return total, modified, errors

if __name__ == "__main__":
    print("=" * 80)
    print("姝ｇ‘淇Python鏂囦欢缂栫爜澹版槑")
    print("=" * 80)

    backend_dir = os.path.dirname(os.path.abspath(__file__))

    # 澶勭悊涓昏鐩綍
    directories = [
        os.path.join(backend_dir, 'app'),
        os.path.join(backend_dir, 'config'),
        os.path.join(backend_dir, 'scripts'),
    ]

    total_all = 0
    modified_all = 0
    errors_all = 0

    for directory in directories:
        if os.path.exists(directory):
            t, m, e = process_directory(directory)
            total_all += t
            modified_all += m
            errors_all += e

    # 澶勭悊鏍圭洰褰曠殑Python鏂囦欢
    for file in ['main.py']:
        file_path = os.path.join(backend_dir, file)
        if os.path.exists(file_path):
            changed, msg = fix_file_encoding(file_path)
            total_all += 1
            if changed:
                modified_all += 1
                print(f"[淇敼] {file}: {msg}")

    print("\n" + "=" * 80)
    print(f"瀹屾垚锛佹€昏{total_all}涓枃浠? 淇敼{modified_all}涓? 閿欒{errors_all}涓?)
    print("=" * 80)