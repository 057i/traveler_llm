import os
import re

def remove_encoding_lines(file_path):
    """移除文件中所有的编码声明行"""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        # 移除编码声明（各种形式）

        # 写回
        with open(file_path, 'w', encoding='utf-8', newline='\n') as f:
            f.write(content)

        return True
    except Exception as e:
        print(f"错误: {file_path} - {e}")
        return False

def process_directory(directory):
    count = 0
    for root, dirs, files in os.walk(directory):
        dirs[:] = [d for d in dirs if d not in ['.venv', '__pycache__', '.git', 'node_modules']]

        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                if remove_encoding_lines(file_path):
                    count += 1
                    if count % 10 == 0:
                        print(f"已处理 {count} 个文件...")

    return count

if __name__ == "__main__":
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    print(f"开始强力清理 {backend_dir}")
    total = process_directory(backend_dir)
    print(f"完成！共处理 {total} 个Python文件")