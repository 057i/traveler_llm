"""
Milvus诊断和修复工具
"""
import subprocess
import sys
import time

# 设置UTF-8编码
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


def run_command(cmd):
    """运行命令并返回结果"""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='ignore',
            timeout=30
        )
        return result.returncode, result.stdout or "", result.stderr or ""
    except subprocess.TimeoutExpired:
        return -1, "", "命令超时"
    except Exception as e:
        return -1, "", str(e)


def check_docker():
    """检查Docker是否运行"""
    print("\n[1/5] 检查Docker状态...")
    code, stdout, stderr = run_command("docker version")

    if code == 0:
        print("  ✓ Docker运行正常")
        return True
    else:
        print("  ✗ Docker未运行或未安装")
        print(f"  错误: {stderr}")
        print("\n解决方法:")
        print("  1. 打开Docker Desktop")
        print("  2. 等待Docker完全启动")
        return False


def check_milvus_container():
    """检查Milvus容器"""
    print("\n[2/5] 检查Milvus容器...")
    code, stdout, stderr = run_command("docker ps -a")

    if "milvus-standalone" in stdout:
        print("  ✓ 找到milvus-standalone容器")

        # 检查容器状态
        if "Up" in stdout and "milvus-standalone" in stdout:
            print("  ✓ 容器正在运行")
            return "running"
        else:
            print("  ! 容器已停止")
            return "stopped"
    else:
        print("  × 容器不存在")
        return "not_exist"


def start_milvus():
    """启动Milvus容器"""
    print("\n[3/5] 启动Milvus容器...")
    code, stdout, stderr = run_command("docker start milvus-standalone")

    if code == 0:
        print("  ✓ 容器启动成功")
        return True
    else:
        print(f"  ✗ 启动失败: {stderr}")
        return False


def create_milvus():
    """创建Milvus容器"""
    print("\n[3/5] 创建Milvus容器...")
    print("  下载镜像中...")

    # 拉取镜像
    code, stdout, stderr = run_command("docker pull milvusdb/milvus:latest")
    if code != 0:
        print(f"  ✗ 拉取镜像失败: {stderr}")
        return False

    print("  ✓ 镜像下载完成")
    print("  创建容器中...")

    # 创建容器
    cmd = """docker run -d --name milvus-standalone -p 19530:19530 -p 9091:9091 -v milvus_data:/var/lib/milvus milvusdb/milvus:latest"""

    code, stdout, stderr = run_command(cmd)

    if code == 0:
        print("  ✓ 容器创建成功")
        return True
    else:
        print(f"  ✗ 创建失败: {stderr}")
        return False


def wait_for_milvus():
    """等待Milvus启动"""
    print("\n[4/5] 等待Milvus服务启动...")
    print("  等待30秒...")

    for i in range(6):
        time.sleep(5)
        print(f"  {(i+1)*5}秒...")

    print("  ✓ 等待完成")


def test_connection():
    """测试Milvus连接"""
    print("\n[5/5] 测试Milvus连接...")

    try:
        from pymilvus import connections
        connections.connect('default', host='localhost', port=19530)
        print("  ✓ Milvus连接成功！")
        return True
    except Exception as e:
        print(f"  ✗ 连接失败: {e}")
        print("\n可能的原因:")
        print("  1. Milvus还在启动中（再等待30秒）")
        print("  2. 端口19530被占用")
        print("  3. Docker网络问题")
        return False


def main():
    """主函数"""
    print("=" * 70)
    print("Milvus诊断和修复工具")
    print("=" * 70)

    # 1. 检查Docker
    if not check_docker():
        print("\n请先启动Docker Desktop，然后重新运行此脚本")
        input("\n按Enter退出...")
        return

    # 2. 检查容器
    status = check_milvus_container()

    # 3. 根据状态处理
    if status == "running":
        print("\nMilvus已在运行中")
    elif status == "stopped":
        if not start_milvus():
            print("\n启动失败，请查看错误信息")
            input("\n按Enter退出...")
            return
    elif status == "not_exist":
        if not create_milvus():
            print("\n创建失败，请查看错误信息")
            input("\n按Enter退出...")
            return

    # 4. 等待启动
    wait_for_milvus()

    # 5. 测试连接
    if test_connection():
        print("\n" + "=" * 70)
        print("✓✓✓ Milvus启动成功！")
        print("=" * 70)
        print("\n下一步:")
        print("  1. cd backend")
        print("  2. python clean_milvus.py (清空旧数据)")
        print("  3. python main.py (启动后端)")
    else:
        print("\n" + "=" * 70)
        print("⚠ Milvus可能还在启动中")
        print("=" * 70)
        print("\n建议:")
        print("  1. 再等待30秒")
        print("  2. 运行: python test_milvus_connection.py")
        print("  3. 查看Docker日志: docker logs milvus-standalone")

    input("\n按Enter退出...")


if __name__ == "__main__":
    main()
