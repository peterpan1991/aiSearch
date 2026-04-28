"""
文件服务模块 - 处理文件扫描和管理
"""
import os
from pathlib import Path
from typing import List
from models.file_item import FileItem
import config


class FileService:
    """文件服务类"""

    def __init__(self):
        self.supported_extensions = config.SUPPORTED_EXTENSIONS

    def scan_folder(self, folder_path: str) -> List[FileItem]:
        """
        扫描文件夹，返回所有支持的文件

        Args:
            folder_path: 文件夹路径

        Returns:
            FileItem列表
        """
        files = []
        folder = Path(folder_path)

        if not folder.exists() or not folder.is_dir():
            return files

        for root, dirs, filenames in os.walk(folder):
            for filename in filenames:
                file_path = os.path.join(root, filename)
                ext = Path(filename).suffix.lower()

                if ext in self.supported_extensions:
                    files.append(FileItem(file_path, ext))

        return files

    def is_image(self, file_path: str) -> bool:
        """判断是否为图片文件"""
        ext = Path(file_path).suffix.lower()
        return ext in config.IMAGE_EXTENSIONS

    def is_video(self, file_path: str) -> bool:
        """判断是否为视频文件"""
        ext = Path(file_path).suffix.lower()
        return ext in config.VIDEO_EXTENSIONS

    def is_document(self, file_path: str) -> bool:
        """判断是否为文档文件"""
        ext = Path(file_path).suffix.lower()
        return ext in config.DOCUMENT_EXTENSIONS
