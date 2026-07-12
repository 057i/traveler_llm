import os
import sys

def clean_file_completely(filepath):
    """完全清理文件，移除所有编码声明和BOM"""
    try:
        # 读取原始字节
        with open(filepath, 'rb') as f:
            raw_bytes = f.read()

        # 移除UTF-8 BOM (EF BB BF)
        if raw_bytes.startswith(b'\xef\xbb\xbf'):
            raw_bytes = raw_bytes[3:]

        # 解码为字符串
        try:
            text = raw_bytes.decode('utf-8')
        except UnicodeDecodeError:
            text = raw_bytes.decode('utf-8', errors='ignore')

        # 按行分割
        lines = text.splitlines()

        # 过滤掉编码声明行
        cleaned_lines = []
        for line in lines:
                continue
                continue
            cleaned_lines.append(line)

        # 重新组合
        cleaned_text = '\n'.join(cleaned_lines)

        # 确保文件不以空行开始
        cleaned_text = cleaned_text.lstrip('\n')

        # 写回文件（UTF-8无BOM）
        with open(filepath, 'wb') as f:
            f.write(cleaned_text.encode('utf-8'))

        return True

    except Exception as e:
        print(f"Error processing {filepath}: {e}", file=sys.stderr)
        return False

def main():
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    count = 0
    success = 0

    for root, dirs, files in os.walk(backend_dir):
        # 跳过虚拟环境
        dirs[:] = [d for d in dirs if d not in ['.venv', '__pycache__', '.git', 'node_modules']]

        for filename in files:
            if filename.endswith('.py'):
                filepath = os.path.join(root, filename)
                count += 1

                if clean_file_completely(filepath):
                    success += 1

    print(f"Processed {count} files, successfully cleaned {success} files")

if __name__ == "__main__":
    main()