"""
鎵归噺淇Python鏂囦欢缂栫爜闂骞舵坊鍔犱腑鏂囨敞閲婄殑鑴氭湰
"""
import os
import sys

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 瀹氫箟闇€瑕佸鐞嗙殑鐩綍
TARGET_DIRS = [
    r"E:\澶фā鍨嬪紑鍙慭浠ｇ爜\缃戠珯\travel_proj\backend\app\api",
    r"E:\澶фā鍨嬪紑鍙慭浠ｇ爜\缃戠珯\travel_proj\backend\app\core",
    r"E:\澶фā鍨嬪紑鍙慭浠ｇ爜\缃戠珯\travel_proj\backend\app\services",
    r"E:\澶фā鍨嬪紑鍙慭浠ｇ爜\缃戠珯\travel_proj\backend\app\workflows",
    r"E:\澶фā鍨嬪紑鍙慭浠ｇ爜\缃戠珯\travel_proj\backend\config",
]


def fix_encoding(file_path):
    """
    淇鏂囦欢鐨勭紪鐮侀棶棰?
    灏濊瘯浠ヤ笉鍚岀紪鐮佽鍙栨枃浠讹紝濡傛灉鏄疓BK缂栫爜鐨刄TF-8瀛楃锛堜贡鐮侊級锛屽垯淇

    Args:
        file_path (str): 鏂囦欢璺緞

    Returns:
        Tuple[bool, str]: (鏄惁淇鎴愬姛, 閿欒淇℃伅)
    """
    try:
        # 璇诲彇鍘熷瀛楄妭
        with open(file_path, 'rb') as f:
            raw_bytes = f.read()

        # 灏濊瘯UTF-8瑙ｇ爜
        try:
            content = raw_bytes.decode('utf-8')

            # 妫€鏌ユ槸鍚︽湁涔辩爜瀛楃
            has_garbled = any(char in content for char in ['閸?, '閹?, '閺?, '閺?, '閼?, '闁?])

            if has_garbled:
                # 灏濊瘯淇锛氬皢鍐呭褰撲綔Latin-1璇诲彇锛屽啀浠TF-8鍐欏叆
                return False, "鍐呭宸叉槸涔辩爜锛岄渶瑕佹墜鍔ㄤ慨澶?
            else:
                # 鏂囦欢姝ｅ父
                return True, "姝ｅ父"

        except UnicodeDecodeError:
            try:
                content = raw_bytes.decode('gbk')
                # 閲嶆柊浠TF-8淇濆瓨
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                return True, "宸蹭粠GBK杞崲涓篣TF-8"
            except:
                return False, "鏃犳硶璇嗗埆缂栫爜"

    except Exception as e:
        return False, f"澶勭悊澶辫触: {str(e)}"


def process_directory(directory):
    """
    澶勭悊鐩綍涓嬬殑鎵€鏈塒ython鏂囦欢

    Args:
        directory (str): 鐩綍璺緞

    Returns:
        dict: 澶勭悊缁撴灉缁熻
    """
    results = {
        'total': 0,
        'fixed': 0,
        'normal': 0,
        'failed': 0,
        'garbled': 0,
        'details': []
    }

    if not os.path.exists(directory):
        print(f"[璀﹀憡] 鐩綍涓嶅瓨鍦? {directory}")
        return results

    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                results['total'] += 1

                success, message = fix_encoding(file_path)

                if success and "杞崲" in message:
                    results['fixed'] += 1
                    status = "[淇]"
                elif success:
                    results['normal'] += 1
                    status = "[姝ｅ父]"
                elif "涔辩爜" in message:
                    results['garbled'] += 1
                    status = "[涔辩爜]"
                else:
                    results['failed'] += 1
                    status = "[澶辫触]"

                results['details'].append({
                    'file': file_path,
                    'status': status,
                    'message': message
                })

                print(f"{status} {os.path.basename(file_path)}: {message}")

    return results


def main():
    """涓诲嚱鏁?""
    print("=" * 80)
    print("寮€濮嬫壒閲忔鏌ython鏂囦欢缂栫爜")
    print("=" * 80)

    all_results = {
        'total': 0,
        'fixed': 0,
        'normal': 0,
        'failed': 0,
        'garbled': 0
    }

    garbled_files = []

    for directory in TARGET_DIRS:
        print(f"\n澶勭悊鐩綍: {directory}")
        print("-" * 80)

        results = process_directory(directory)

        all_results['total'] += results['total']
        all_results['fixed'] += results['fixed']
        all_results['normal'] += results['normal']
        all_results['failed'] += results['failed']
        all_results['garbled'] += results['garbled']

        # 鏀堕泦涔辩爜鏂囦欢
        for detail in results['details']:
            if detail['status'] == '[涔辩爜]':
                garbled_files.append(detail['file'])

        print(f"\n鐩綍缁熻:")
        print(f"  鎬绘枃浠舵暟: {results['total']}")
        print(f"  宸蹭慨澶? {results['fixed']}")
        print(f"  姝ｅ父: {results['normal']}")
        print(f"  涔辩爜: {results['garbled']}")
        print(f"  澶辫触: {results['failed']}")

    print("\n" + "=" * 80)
    print("鎬讳綋缁熻:")
    print(f"  鎬绘枃浠舵暟: {all_results['total']}")
    print(f"  宸蹭慨澶? {all_results['fixed']}")
    print(f"  姝ｅ父: {all_results['normal']}")
    print(f"  涔辩爜: {all_results['garbled']}")
    print(f"  澶辫触: {all_results['failed']}")
    print("=" * 80)

    if garbled_files:
        print("\n闇€瑕佹墜鍔ㄤ慨澶嶇殑涔辩爜鏂囦欢鍒楄〃:")
        for f in garbled_files:
            print(f"  - {f}")


if __name__ == "__main__":
    main()