import os
import sys

def clean_encoding_declarations(directory):
    """
    清理所有Python文件中的编码声明
    Python 3默认使用UTF-8，不需要编码声明
    """
    count = 0
    for root, dirs, files in os.walk(directory):
        # 跳过虚拟环境
        dirs[:] = [d for d in dirs if d not in ['.venv', '__pycache__', '.git']]

        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        lines = f.readlines()

                    # 过滤掉编码声明行
                    new_lines = []
                    for line in lines:
                        # 跳过编码声明和BOM
                            continue
                        new_lines.append(line)

                    # 写回文件
                    with open(file_path, 'w', encoding='utf-8', newline='\n') as f:
                        f.writelines(new_lines)

                    count += 1
                    if count % 10 == 0:
                        print(f"已处理 {count} 个文件...")

                except Exception as e:
                    print(f"处理文件失败: {file_path}, 错误: {e}")

    return count

if __name__ == "__main__":
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    print(f"开始清理 {backend_dir}")
    total = clean_encoding_declarations(backend_dir)
    print(f"完成！共处理 {total} 个Python文件")