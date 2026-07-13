"""
MinerU Client - 重写版本
使用 mineru.net API v4
"""
import time
import requests
from typing import Dict, Any, Optional
from loguru import logger
import os


class MinerUClientV2:
    """MinerU API v4 客户端（重写版）"""

    def __init__(self):
        self.token = os.getenv("MINERU_API_TOKEN")
        self.base_url = os.getenv("MINERU_BASE_URL", "https://mineru.net/api/v4")

        if not self.token:
            raise ValueError("MINERU_API_TOKEN not set in environment")

        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.token}"
        }

        # 禁用代理
        self.session = requests.Session()
        self.session.trust_env = False

        logger.info(f"[MinerU] Initialized with base_url: {self.base_url}")

    def parse_by_file(self, file_path: str, timeout: int = 600) -> Dict[str, Any]:
        """
        解析PDF文件（完整流程）

        Args:
            file_path: PDF文件路径
            timeout: 超时时间（秒）

        Returns:
            {"markdown": str, "pages_count": int, "raw_text": str}
        """
        try:
            # Step 1: 上传文件获取batch_id
            batch_id = self._upload_file(file_path)

            if not batch_id:
                raise RuntimeError("上传失败，未获取到batch_id")

            # Step 2: 轮询进度获取结果
            result = self._poll_progress(batch_id, timeout)

            return result

        except Exception as e:
            logger.error(f"[MinerU] 解析失败: {e}")
            raise

    def _upload_file(self, file_path: str) -> str:
        """
        Step 1: 上传文件到MinerU

        Returns:
            batch_id
        """
        file_name = os.path.basename(file_path)
        logger.info(f"[MinerU] 开始上传文件: {file_name}")

        # 1. 获取上传URL
        url = f"{self.base_url}/file-urls/batch"
        data = {
            "files": [{"name": file_name}],
            "model_version": "vlm"
        }

        try:
            response = self.session.post(url, headers=self.headers, json=data, timeout=30)
            logger.info(f"[MinerU] 获取上传URL响应: {response.status_code}")

            if response.status_code != 200:
                logger.error(f"[MinerU] 获取上传URL失败: {response.text}")
                raise RuntimeError(f"获取上传URL失败: {response.status_code}")

            resp_data = response.json()
            logger.info(f"[MinerU] 上传URL响应数据: {resp_data}")

            if resp_data.get("code") != 0:
                raise RuntimeError(f"API返回错误: {resp_data.get('message')}")

            upload_info = resp_data["data"]
            file_url = upload_info["file_urls"][0]
            batch_id = upload_info["batch_id"]

            logger.info(f"[MinerU] 获取到batch_id: {batch_id}")
            logger.info(f"[MinerU] 上传URL: {file_url[:100]}...")

            # 2. 上传文件到预签名URL
            with open(file_path, 'rb') as f:
                upload_response = self.session.put(file_url, data=f, timeout=300)

            if upload_response.status_code == 200:
                logger.success(f"[MinerU] 文件上传成功")
            else:
                logger.error(f"[MinerU] 文件上传失败: {upload_response.status_code}")
                raise RuntimeError(f"文件上传失败: {upload_response.status_code}")

            return batch_id

        except requests.exceptions.Timeout:
            logger.error(f"[MinerU] 上传超时")
            raise
        except Exception as e:
            logger.error(f"[MinerU] 上传失败: {e}")
            raise

    def _poll_progress(self, batch_id: str, timeout: int = 600) -> Dict[str, Any]:
        """
        Step 2: 轮询解析进度

        Args:
            batch_id: 批次ID
            timeout: 超时时间（秒）

        Returns:
            {"markdown": str, "pages_count": int}
        """
        url = f"{self.base_url}/extract-results/batch/{batch_id}"
        interval = 3  # 轮询间隔（秒）
        start_time = time.time()

        logger.info(f"[MinerU] 开始轮询进度: batch_id={batch_id}")

        while True:
            # 检查超时
            elapsed = time.time() - start_time
            if elapsed > timeout:
                logger.error(f"[MinerU] 轮询超时（{timeout}秒）")
                raise TimeoutError(f"MinerU轮询超时")

            time.sleep(interval)

            try:
                response = self.session.get(url, headers=self.headers, timeout=10)
                logger.info(f"[MinerU] [{int(elapsed)}s] 轮询响应: {response.status_code}")

                if response.status_code != 200:
                    logger.warning(f"[MinerU] [{int(elapsed)}s] 非200状态码: {response.status_code}")
                    continue

                resp_data = response.json()

                # 打印完整响应（调试用）
                logger.info(f"[MinerU] [{int(elapsed)}s] 响应数据: {resp_data}")

                if resp_data.get("code") != 0:
                    logger.warning(f"[MinerU] [{int(elapsed)}s] code非0: {resp_data.get('message')}")
                    continue

                # 解析结果
                extract_result = resp_data["data"].get("extract_result", [])

                if not extract_result or len(extract_result) == 0:
                    logger.info(f"[MinerU] [{int(elapsed)}s] 结果为空，继续轮询...")
                    continue

                result = extract_result[0]
                state = result.get("state", "unknown")

                logger.info(f"[MinerU] [{int(elapsed)}s] 当前状态: {state}")

                if state == "done":
                    logger.success(f"[MinerU] [{int(elapsed)}s] 解析完成")
                    return self._extract_result(result)

                elif state == "failed":
                    err_msg = result.get("err_msg", "未知错误")
                    logger.error(f"[MinerU] 解析失败: {err_msg}")
                    raise RuntimeError(f"MinerU解析失败: {err_msg}")

                elif state in ["processing", "queue", "waiting"]:
                    logger.info(f"[MinerU] [{int(elapsed)}s] {state}中...")
                    continue

                else:
                    logger.warning(f"[MinerU] [{int(elapsed)}s] 未知状态: {state}")
                    continue

            except requests.exceptions.Timeout:
                logger.warning(f"[MinerU] [{int(elapsed)}s] 请求超时，继续...")
                continue
            except Exception as e:
                logger.error(f"[MinerU] [{int(elapsed)}s] 轮询错误: {e}")
                # 不中断，继续轮询
                continue

    def _extract_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        从API响应中提取结果

        Returns:
            {"markdown": str, "pages_count": int, "raw_text": str}
        """
        logger.info("[MinerU] ========== 提取解析结果 ==========")
        logger.info(f"[MinerU] 结果keys: {list(result.keys())}")

        # 打印所有字段
        for key, value in result.items():
            if isinstance(value, str) and len(value) > 100:
                logger.info(f"[MinerU] {key}: {len(value)} 字符")
                logger.info(f"[MinerU] {key} 前200字符: {value[:200]}")
            else:
                logger.info(f"[MinerU] {key}: {value}")

        logger.info("[MinerU] ======================================")

        # 检查是否有ZIP下载URL
        full_zip_url = result.get('full_zip_url')

        if full_zip_url:
            logger.info(f"[MinerU] 发现ZIP下载URL，开始下载并解压...")
            return self._download_and_extract_zip(full_zip_url)

        # 如果没有ZIP，尝试直接提取字段
        markdown = (
            result.get('markdown') or
            result.get('md_content') or
            result.get('content') or
            result.get('text') or
            ''
        )

        raw_text = result.get('raw_text', '')
        pages_count = result.get('pages_count', 0)

        logger.info(f"[MinerU] 提取结果:")
        logger.info(f"[MinerU]   - Markdown: {len(markdown)} 字符")
        logger.info(f"[MinerU]   - Raw text: {len(raw_text)} 字符")
        logger.info(f"[MinerU]   - Pages: {pages_count}")

        if len(markdown) > 0:
            logger.info(f"[MinerU] Markdown前500字符:\n{markdown[:500]}")

        return {
            "markdown": markdown,
            "raw_text": raw_text,
            "pages_count": pages_count
        }

    def _download_and_extract_zip(self, zip_url: str) -> Dict[str, Any]:
        """
        下载并解压ZIP文件，提取Markdown

        Args:
            zip_url: ZIP文件下载URL

        Returns:
            {"markdown": str, "pages_count": int, "raw_text": str}
        """
        import zipfile
        import tempfile
        from pathlib import Path

        logger.info(f"[MinerU] 下载ZIP: {zip_url[:100]}...")

        try:
            # 下载ZIP
            response = self.session.get(zip_url, timeout=60)

            if response.status_code != 200:
                logger.error(f"[MinerU] 下载ZIP失败: {response.status_code}")
                raise RuntimeError(f"下载ZIP失败: {response.status_code}")

            logger.success(f"[MinerU] ZIP下载成功: {len(response.content)} 字节")

            # 保存到临时文件
            with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as tmp_zip:
                tmp_zip.write(response.content)
                tmp_zip_path = tmp_zip.name

            logger.info(f"[MinerU] ZIP保存到: {tmp_zip_path}")

            # 解压ZIP
            extract_dir = Path(tempfile.mkdtemp())
            logger.info(f"[MinerU] 解压到: {extract_dir}")

            with zipfile.ZipFile(tmp_zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)

            logger.success(f"[MinerU] ZIP解压成功")

            # 查找MD文件
            md_files = list(extract_dir.rglob("*.md"))

            if not md_files:
                logger.error(f"[MinerU] ZIP中未找到MD文件")
                raise RuntimeError("ZIP中未找到MD文件")

            logger.info(f"[MinerU] 找到 {len(md_files)} 个MD文件")

            # 读取第一个MD文件（通常是主文件）
            md_file = md_files[0]
            logger.info(f"[MinerU] 读取MD文件: {md_file.name}")

            with open(md_file, 'r', encoding='utf-8') as f:
                markdown = f.read()

            logger.success(f"[MinerU] MD文件读取成功: {len(markdown)} 字符")

            if len(markdown) > 0:
                logger.info(f"[MinerU] Markdown前500字符:\n{markdown[:500]}")

            # 清理临时文件
            import shutil
            shutil.rmtree(extract_dir, ignore_errors=True)
            Path(tmp_zip_path).unlink(missing_ok=True)

            return {
                "markdown": markdown,
                "raw_text": "",
                "pages_count": 0
            }

        except Exception as e:
            logger.error(f"[MinerU] 下载解压ZIP失败: {e}")
            raise

    def __del__(self):
        """清理资源"""
        if hasattr(self, 'session'):
            self.session.close()


# 全局单例
_mineru_client_v2 = None


def get_mineru_client_v2() -> MinerUClientV2:
    """获取MinerU客户端（单例）"""
    global _mineru_client_v2
    if _mineru_client_v2 is None:
        _mineru_client_v2 = MinerUClientV2()
    return _mineru_client_v2
