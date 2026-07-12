"""
批量修复所有Python文件的中文乱码问题
通过识别常见乱码模式并替换为正确的中文
"""
import os
import re
from pathlib import Path


# 常见乱码模式映射
COMMON_FIXES = {
    # 日志相关
    '鍒濆鍖': '初始化',
    '璇嗗埆': '识别',
    '澶勭悊': '处理',
    '鎴愬姛': '成功',
    '澶辫触': '失败',
    '閿欒': '错误',
    '璀﹀憡': '警告',
    '淇℃伅': '信息',
    '寮€濮': '开始',
    '缁撴潫': '结束',
    '杩炴帴': '连接',
    '鏂紑': '断开',

    # API相关
    '鎺ㄨ崘': '推荐',
    '鏌ヨ': '查询',
    '鎼滅储': '搜索',
    '涓婁紶': '上传',
    '涓嬭浇': '下载',
    '鍒犻櫎': '删除',
    '鏇存柊': '更新',
    '鍒涘缓': '创建',
    '鑾峰彇': '获取',

    # 数据相关
    '鏁版嵁': '数据',
    '缁撴灉': '结果',
    '鍒楄〃': '列表',
    '璇︾粏': '详细',
    '杩涘害': '进度',
    '鐘舵€': '状态',
    '浠诲姟': '任务',

    # 系统相关
    '鏈嶅姟': '服务',
    '绯荤粺': '系统',
    '閰嶇疆': '配置',
    '鍚姩': '启动',
    '鍏抽棴': '关闭',
    '鍋滄': '停止',
    '閲嶅惎': '重启',

    # 文件相关
    '鏂囦欢': '文件',
    '璺緞': '路径',
    '鍚嶇О': '名称',
    '绫诲瀷': '类型',
    '澶у皬': '大小',
    '淇濆瓨': '保存',
    '鍔犺浇': '加载',

    # 其他
    '瀹屾垚': '完成',
    '璇疯姹': '请求',
    '鍝嶅簲': '响应',
    '瓒呮椂': '超时',
    '閲嶈瘯': '重试',
    '璺宠繃': '跳过',
    '蹇界暐': '忽略',

    # Redis连接日志特定
    '杩炴帴鎴愬姛': '连接成功',
    '杩炴帴澶辫触': '连接失败',
}


def fix_chinese_encoding(text: str) -> str:
    """修复中文乱码"""
    # 应用映射表
    for broken, correct in COMMON_FIXES.items():
        text = text.replace(broken, correct)

    # 移除残留的Unicode escape
    text = re.sub(r'\\u[0-9a-fA-F]{4}', '', text)
    text = re.sub(r'\\x[0-9a-fA-F]{2}', '', text)

    return text


def process_file(file_path: Path) -> bool:
    """处理单个文件"""
    try:
        # 读取文件
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        # 检查是否有乱码
        if not any(broken in content for broken in COMMON_FIXES.keys()):
            return False

        # 修复乱码
        fixed_content = fix_chinese_encoding(content)

        # 写回文件
        with open(file_path, 'w', encoding='utf-8', newline='\n') as f:
            f.write(fixed_content)

        return True

    except Exception as e:
        print(f"处理失败 {file_path}: {e}")
        return False


def main():
    """主函数"""
    backend_dir = Path(__file__).parent

    # 统计
    total = 0
    fixed = 0

    print("=" * 80)
    print("开始修复中文乱码")
    print("=" * 80)

    # 遍历所有Python文件
    for py_file in backend_dir.rglob("*.py"):
        # 跳过虚拟环境
        if '.venv' in py_file.parts or '__pycache__' in py_file.parts:
            continue

        total += 1

        if process_file(py_file):
            fixed += 1
            rel_path = py_file.relative_to(backend_dir)
            print(f"✅ 修复: {rel_path}")

    print("=" * 80)
    print(f"完成！共扫描 {total} 个文件，修复 {fixed} 个文件")
    print("=" * 80)


if __name__ == "__main__":
    main()
