"""
MinerU API Client

Official API client for MinerU document parsing service
https://mineru.net
"""
import requests
import time
from loguru import logger
from typing import Optional, Dict, Any
from config.settings import settings


class MinerUClient:
    """MinerU API客户端"""

    BASE_URL = "https://mineru.net/api/v1/agent"

    def __init__(self, api_key: Optional[str] = None):
        """
        初始化MinerU客户端

        Args:
            api_key: API密钥（可选，从settings读取）
        """
        self.api_key = api_key or settings.MINERU_API_KEY
        self.timeout = settings.MINERU_TIMEOUT

    def parse_by_file(
        self,
        file_path: str,
        language: str = "ch",
        page_range: Optional[str] = None,
        enable_table: bool = True,
        is_ocr: bool = False,
        enable_formula: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        通过文件上传提交文档解析任务并等待结果

        Args:
            file_path: 本地PDF文件路径
            language: 语言设置 ("ch"中文, "en"英文)
            page_range: 页码范围，如 "1-5"
            enable_table: 是否解析表格
            is_ocr: 是否启用OCR
            enable_formula: 是否解析公式

        Returns:
            解析后的Markdown文本，失败返回None
        """
        logger.info(f"[MinerU] 开始解析文件: {file_path}")

        try:
            # 1. 创建解析任务并获取上传URL
            task_id, file_url = self._create_parse_task(
                file_path=file_path,
                language=language,
                page_range=page_range,
                enable_table=enable_table,
                is_ocr=is_ocr,
                enable_formula=enable_formula
            )

            if not task_id or not file_url:
                return None

            # 2. 上传文件到OSS
            if not self._upload_file(file_path, file_url):
                return None

            logger.info("[MinerU] 文件上传成功，等待解析...")

            # 3. 轮询等待解析结果
            markdown_content = self._poll_result(task_id)

            return markdown_content

        except Exception as e:
            logger.error(f"[MinerU] 解析失败: {e}")
            return None

    def _create_parse_task(
        self,
        file_path: str,
        language: str,
        page_range: Optional[str],
        enable_table: bool,
        is_ocr: bool,
        enable_formula: bool
    ) -> tuple[Optional[str], Optional[str]]:
        """
        创建解析任务并获取上传URL

        Returns:
            (task_id, file_url) 元组，失败返回 (None, None)
        """
        try:
            import os
            file_name = os.path.basename(file_path)

            # 构建请求数据
            data = {
                "file_name": file_name,
                "language": language,
                "enable_table": enable_table,
                "is_ocr": is_ocr,
                "enable_formula": enable_formula
            }

            if page_range:
                data["page_range"] = page_range

            # 发送请求
            url = f"{self.BASE_URL}/parse/file"
            headers = {}

            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"

            logger.info(f"[MinerU] 创建解析任务: {url}")

            response = requests.post(url, json=data, headers=headers, timeout=30)
            result = response.json()

            if result.get("code") != 0:
                error_msg = result.get("msg", "未知错误")
                logger.error(f"[MinerU] 获取上传链接失败: {error_msg}")
                return None, None

            task_id = result["data"]["task_id"]
            file_url = result["data"]["file_url"]

            logger.success(f"[MinerU] 任务已创建, task_id: {task_id}")

            return task_id, file_url

        except Exception as e:
            logger.error(f"[MinerU] 创建任务失败: {e}")
            return None, None

    def _upload_file(self, file_path: str, file_url: str) -> bool:
        """
        上传文件到OSS

        Args:
            file_path: 本地文件路径
            file_url: OSS上传URL

        Returns:
            上传是否成功
        """
        try:
            logger.info("[MinerU] 正在上传文件到OSS...")

            with open(file_path, "rb") as f:
                response = requests.put(file_url, data=f, timeout=120)

                if response.status_code not in (200, 201):
                    logger.error(f"[MinerU] 文件上传失败, HTTP {response.status_code}")
                    return False

            logger.success("[MinerU] 文件上传成功")
            return True

        except Exception as e:
            logger.error(f"[MinerU] 上传文件失败: {e}")
            return False

    def _poll_result(
        self,
        task_id: str,
        timeout: Optional[int] = None,
        interval: int = 3
    ) -> Optional[Dict[str, Any]]:
        """
        轮询查询解析结果

        Args:
            task_id: 任务ID
            timeout: 超时时间（秒），默认使用settings配置
            interval: 轮询间隔（秒）

        Returns:
            包含markdown_content和output_directory的字典，失败返回None
        """
        if timeout is None:
            timeout = self.timeout

        state_labels = {
            "pending": "排队中",
            "running": "解析中",
            "waiting-file": "等待文件上传",
        }

        start_time = time.time()

        while time.time() - start_time < timeout:
            try:
                elapsed = int(time.time() - start_time)

                # 查询任务状态
                url = f"{self.BASE_URL}/parse/{task_id}"
                headers = {}

                if self.api_key:
                    headers["Authorization"] = f"Bearer {self.api_key}"

                response = requests.get(url, headers=headers, timeout=30)
                result = response.json()

                state = result["data"]["state"]

                # 解析完成
                if state == "done":
                    markdown_url = result["data"].get("markdown_url")
                    logger.success(f"[MinerU] [{elapsed}s] 解析完成")

                    if not markdown_url:
                        logger.error("[MinerU] 未找到markdown_url")
                        return None

                    # 下载Markdown内容
                    md_response = requests.get(markdown_url, timeout=60)
                    markdown_content = md_response.text

                    logger.info(f"[MinerU] 获取Markdown内容: {len(markdown_content)} 字符")

                    # 检查是否有完整输出包（ZIP）
                    result_url = result["data"].get("result_url")
                    output_directory = None

                    logger.info(f"[MinerU] result_url存在: {result_url is not None}")

                    if result_url:
                        try:
                            import tempfile
                            import zipfile
                            import os

                            # 创建临时目录
                            output_directory = tempfile.mkdtemp(prefix=f"mineru_{task_id}_")
                            zip_path = os.path.join(output_directory, "result.zip")

                            logger.info(f"[MinerU] 临时目录: {output_directory}")

                            # 下载ZIP包
                            logger.info(f"[MinerU] 正在下载完整输出包...")
                            zip_response = requests.get(result_url, timeout=180)
                            with open(zip_path, 'wb') as f:
                                f.write(zip_response.content)

                            logger.info(f"[MinerU] ZIP下载完成: {os.path.getsize(zip_path)} 字节")

                            # 解压
                            logger.info(f"[MinerU] 正在解压输出包...")
                            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                                zip_ref.extractall(output_directory)

                            os.remove(zip_path)  # 删除ZIP文件

                            # 列出解压后的文件
                            file_count = sum([len(files) for r, d, files in os.walk(output_directory)])
                            logger.success(f"[MinerU] 输出包已解压: {output_directory} ({file_count}个文件)")

                        except Exception as e:
                            logger.warning(f"[MinerU] 下载输出包失败: {e}")
                            output_directory = None
                    else:
                        logger.info(f"[MinerU] API未返回result_url，只有Markdown文本")

                    # 返回完整结果
                    return {
                        "markdown_content": markdown_content,
                        "output_directory": output_directory,
                        "has_output_package": output_directory is not None
                    }

                # 解析失败
                if state == "failed":
                    error_msg = result["data"].get("err_msg", "未知错误")
                    logger.error(f"[MinerU] [{elapsed}s] 解析失败: {error_msg}")
                    return None

                # 仍在处理中
                status_text = state_labels.get(state, state)
                logger.info(f"[MinerU] [{elapsed}s] {status_text}...")

                time.sleep(interval)

            except Exception as e:
                logger.error(f"[MinerU] 轮询出错: {e}")
                time.sleep(interval)

        # 超时
        logger.warning(f"[MinerU] 轮询超时 ({timeout}s)，task_id: {task_id}")
        logger.warning("[MinerU] 请稍后手动查询任务状态")

        return None

    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        查询任务状态

        Args:
            task_id: 任务ID

        Returns:
            任务状态信息
        """
        try:
            url = f"{self.BASE_URL}/parse/{task_id}"
            headers = {}

            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"

            response = requests.get(url, headers=headers, timeout=30)
            result = response.json()

            return result.get("data")

        except Exception as e:
            logger.error(f"[MinerU] 查询任务状态失败: {e}")
            return None


# 单例实例
_mineru_client: Optional[MinerUClient] = None


def get_mineru_client() -> MinerUClient:
    """获取MinerU客户端单例"""
    global _mineru_client

    if _mineru_client is None:
        _mineru_client = MinerUClient()

    return _mineru_client
