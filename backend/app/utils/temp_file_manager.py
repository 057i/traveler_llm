"""
Temporary File Manager

管理文档处理过程中的临时文件
"""
import os
import shutil
from pathlib import Path
from loguru import logger
from typing import Optional


class TempFileManager:
    """临时文件管理器"""

    def __init__(self, base_dir: str = "./temp_uploads"):
        """
        初始化临时文件管理器

        Args:
            base_dir: 临时文件基础目录
        """
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def create_temp_dir(self, doc_id: str) -> Path:
        """
        为文档创建临时目录

        Args:
            doc_id: 文档ID

        Returns:
            临时目录路径
        """
        temp_dir = self.base_dir / doc_id
        temp_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"[TempFile] Created temp directory: {temp_dir}")
        return temp_dir

    def save_uploaded_file(self, doc_id: str, file_content: bytes, filename: str) -> Path:
        """
        保存用户上传的文件到临时目录

        Args:
            doc_id: 文档ID
            file_content: 文件内容
            filename: 文件名

        Returns:
            保存的文件路径
        """
        temp_dir = self.create_temp_dir(doc_id)
        file_path = temp_dir / filename

        with open(file_path, "wb") as f:
            f.write(file_content)

        logger.success(f"[TempFile] Saved uploaded file: {file_path}")
        return file_path

    def save_mineru_output(self, doc_id: str, output_dir: Path) -> Path:
        """
        保存MinerU解析输出到临时目录

        Args:
            doc_id: 文档ID
            output_dir: MinerU输出目录

        Returns:
            临时目录中的输出路径
        """
        temp_dir = self.base_dir / doc_id / "mineru_output"

        if temp_dir.exists():
            shutil.rmtree(temp_dir)

        shutil.copytree(output_dir, temp_dir)
        logger.success(f"[TempFile] Saved MinerU output: {temp_dir}")
        return temp_dir

    def get_temp_dir(self, doc_id: str) -> Optional[Path]:
        """
        获取文档的临时目录

        Args:
            doc_id: 文档ID

        Returns:
            临时目录路径，不存在返回None
        """
        temp_dir = self.base_dir / doc_id
        return temp_dir if temp_dir.exists() else None

    def cleanup_temp_dir(self, doc_id: str) -> bool:
        """
        清理文档的临时目录

        Args:
            doc_id: 文档ID

        Returns:
            是否清理成功
        """
        try:
            temp_dir = self.base_dir / doc_id

            if not temp_dir.exists():
                logger.warning(f"[TempFile] Temp directory not found: {temp_dir}")
                return True

            shutil.rmtree(temp_dir)
            logger.success(f"[TempFile] Cleaned up temp directory: {temp_dir}")
            return True

        except Exception as e:
            logger.error(f"[TempFile] Failed to cleanup temp directory: {e}")
            return False

    def cleanup_all_temp_files(self) -> int:
        """
        清理所有临时文件（可用于定期清理）

        Returns:
            清理的目录数量
        """
        try:
            count = 0
            for item in self.base_dir.iterdir():
                if item.is_dir():
                    shutil.rmtree(item)
                    count += 1

            logger.success(f"[TempFile] Cleaned up {count} temp directories")
            return count

        except Exception as e:
            logger.error(f"[TempFile] Failed to cleanup all temp files: {e}")
            return 0


# ==================== 单例 ====================

_temp_file_manager = None


def get_temp_file_manager() -> TempFileManager:
    """获取临时文件管理器单例"""
    global _temp_file_manager
    if _temp_file_manager is None:
        _temp_file_manager = TempFileManager()
    return _temp_file_manager
