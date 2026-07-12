"""
强力修复所有Python文件的中文乱码
使用常见的乱码模式映射到正确的中文
"""
import os
import re

# 常见乱码到中文的映射表
ENCODING_FIX_MAP = {
    # 常见词汇
    '不在': '不在',
    '白名': '白名',
    '单，': '单，',
    '但扩': '但扩',
    '展名': '展名',
    '正确': '正确',
    '，允': '，允',
    '许通': '许通',
    '过': '过',
    '文件': '文件',
    '类型': '类型',
    '上传': '上传',
    '处理': '处理',
    '推荐': '推荐',
    '查询': '查询',
    '启动': '启动',
    '关闭': '关闭',
    '成功': '成功',
    '失败': '失败',
    '错误': '错误',
    '警告': '警告',
    '信息': '信息',
    '数据': '数据',
    '库连': '库连',
    '接已': '接已',
    '建立': '建立',
    '配置': '配置',
    '初始化': '初始化',
    '加载': '加载',
    '保存': '保存',
    '删除': '删除',
    '更新': '更新',
    '改': '改',
    '识别': '识别',
    '提取': '提取',
    '文本': '文本',
    '图片': '图片',
    '视频': '视频',
    '音频': '音频',

    # Unicode escape sequences
    r'类型': '类型',
    r'在': '在',
    r'正': '正',
    r'确': '确',
    r'通过': '通过',
}

def fix_file_content(content):
    """修复文件内容中的乱码"""
    # 替换映射表中的乱码
    for broken, fixed in ENCODING_FIX_MAP.items():
        content = content.replace(broken, fixed)

    # 移除Unicode escape sequences
    content = re.sub(r'\\u[0-9a-fA-F]{4}', '', content)

    return content

def process_file(filepath):
    """处理单个文件"""
    try:
        # 读取文件
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        # 修复内容
        fixed_content = fix_file_content(content)

        # 如果有变化，写回文件
        if fixed_content != content:
            with open(filepath, 'w', encoding='utf-8', newline='\n') as f:
                f.write(fixed_content)
            return True

        return False
    except Exception as e:
        print(f"Error processing {filepath}: {e}")
        return False

def main():
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    fixed_count = 0
    total_count = 0

    print("开始修复中文乱码...")
    print("="*60)

    for root, dirs, files in os.walk(backend_dir):
        # 跳过虚拟环境
        dirs[:] = [d for d in dirs if d not in ['.venv', '__pycache__', '.git']]

        for filename in files:
            if filename.endswith('.py'):
                filepath = os.path.join(root, filename)
                total_count += 1

                if process_file(filepath):
                    fixed_count += 1
                    rel_path = os.path.relpath(filepath, backend_dir)
                    print(f"✅ 修复: {rel_path}")

    print("="*60)
    print(f"完成！共扫描 {total_count} 个文件，修复 {fixed_count} 个文件")

if __name__ == "__main__":
    main()
