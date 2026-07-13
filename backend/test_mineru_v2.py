"""
测试MinerU V2客户端
"""
import os
import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.mineru_client_v2 import get_mineru_client_v2
from loguru import logger

# 设置环境变量
os.environ["MINERU_API_TOKEN"] = "eyJ0eXBlIjoiSldUIiwiYWxnIjoiSFM1MTIifQ.eyJqdGkiOiIxMzIwMDk5NSIsInJvbCI6IlJPTEVfUkVHSVNURVIiLCJpc3MiOiJPcGVuWExhYiIsImlhdCI6MTc4MTE2NTYzMSwiY2xpZW50SWQiOiJsa3pkeDU3bnZ5MjJqa3BxOXgydyIsInBob25lIjoiIiwib3BlbklkIjpudWxsLCJ1dWlkIjoiODliOTM1OGEtN2Y1ZS00MDRhLWE1YTItYTJhYWFiZjNlZDgzIiwiZW1haWwiOiIiLCJleHAiOjE3ODg5NDE2MzF9.R9eAgDi5v5sm2y6-EFIWaEajKhCUhlm9bXcHhLNemrbzBQPtH6fm1D-64RepfwJrSLZamatrhJKIXb5_bUntAg"
os.environ["MINERU_BASE_URL"] = "https://mineru.net/api/v4"


def test_mineru_v2():
    """测试MinerU V2客户端"""

    # 使用已知的PDF文件
    test_pdf = Path(r"E:\大模型开发\代码\网站\travel_proj\backend\data\uploads\三清山攻略（第七版）.pdf")

    if not test_pdf.exists():
        logger.error(f"测试PDF不存在: {test_pdf}")
        return

    logger.info(f"找到测试PDF: {test_pdf.name}")

    try:
        # 创建客户端
        client = get_mineru_client_v2()

        # 解析PDF
        logger.info("=" * 60)
        logger.info("开始解析PDF...")
        logger.info("=" * 60)

        result = client.parse_by_file(str(test_pdf), timeout=600)

        logger.info("=" * 60)
        logger.info("解析完成！")
        logger.info("=" * 60)

        # 显示结果
        logger.success(f"✅ Markdown长度: {len(result['markdown'])} 字符")
        logger.success(f"✅ Raw text长度: {len(result['raw_text'])} 字符")
        logger.success(f"✅ 页数: {result['pages_count']}")

        if len(result['markdown']) > 0:
            logger.info(f"\nMarkdown前1000字符:\n{result['markdown'][:1000]}")
        else:
            logger.warning("⚠️  Markdown为空！")

        # 保存结果到文件
        output_file = project_root / "test_mineru_result.md"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(result['markdown'])

        logger.success(f"✅ 结果已保存到: {output_file}")

    except TimeoutError as e:
        logger.error(f"❌ 超时: {e}")
    except RuntimeError as e:
        logger.error(f"❌ 运行时错误: {e}")
    except Exception as e:
        logger.error(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    logger.info("========== 测试MinerU V2客户端 ==========")
    test_mineru_v2()
    logger.info("========== 测试完成 ==========")
