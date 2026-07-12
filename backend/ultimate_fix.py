import os
import re

def fix_file(filepath):
    """彻底修复文件"""
    try:
        # 读取原始字节
        with open(filepath, 'rb') as f:
            raw = f.read()

        # 尝试解码
        try:
            content = raw.decode('utf-8')
        except:
            content = raw.decode('utf-8', errors='ignore')

        # 移除BOM
        if content.startswith('﻿'):
            content = content[1:]

        # 分行处理
        lines = content.split('\n')
        new_lines = []

        for line in lines:
            # 跳过编码声明行（任何形式）
                continue
                continue
            new_lines.append(line)

        # 重新组合
        new_content = '\n'.join(new_lines)

        # 写回（UTF-8，无BOM）
        with open(filepath, 'w', encoding='utf-8', newline='\n') as f:
            f.write(new_content)

        return True
    except Exception as e:
        print(f"❌ 失败: {filepath}\n   错误: {e}")
        return False

def main():
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    count = 0
    fixed = 0

    for root, dirs, files in os.walk(backend_dir):
        dirs[:] = [d for d in dirs if d not in ['.venv', '__pycache__', '.git']]

        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                count += 1

                if fix_file(filepath):
                    fixed += 1
                    if fixed % 10 == 0:
                        print(f"✅ 已修复 {fixed}/{count} 个文件...")

    print(f"\n{'='*60}")
    print(f"完成！共扫描 {count} 个文件，成功修复 {fixed} 个")
    print(f"{'='*60}")

if __name__ == "__main__":
    print("开始彻底清理编码问题...")
    print("="*60)
    main()