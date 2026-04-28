"""
文件数据模型
"""
import os
from pathlib import Path
from dataclasses import dataclass
from typing import Optional, List
import config


@dataclass
class FileItem:
    """文件数据模型"""
    path: str
    extension: str
    name: str = ""
    size: int = 0
    ocr_text: Optional[str] = None
    embedding: Optional[List[float]] = None

    def __post_init__(self):
        """初始化派生字段"""
        if not self.name:
            self.name = Path(self.path).name
        if self.size == 0 and os.path.exists(self.path):
            self.size = os.path.getsize(self.path)

    def is_image(self) -> bool:
        """是否为图片"""
        return self.extension in config.IMAGE_EXTENSIONS

    def is_video(self) -> bool:
        """是否为视频"""
        return self.extension in config.VIDEO_EXTENSIONS

    def is_document(self) -> bool:
        """是否为文档"""
        return self.extension in config.DOCUMENT_EXTENSIONS

    def get_size_formatted(self) -> str:
        """获取格式化的大小"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if self.size < 1024:
                return f"{self.size:.2f} {unit}"
            self.size /= 1024
        return f"{self.size:.2f} TB"

    def matches_keyword(self, keyword: str) -> bool:
        """检查是否匹配关键字"""
        if not keyword:
            return True
        keyword_lower = keyword.lower()

        # 检查文件名
        if keyword_lower in self.name.lower():
            return True

        # 检查OCR文本
        if self.ocr_text and keyword_lower in self.ocr_text.lower():
            return True

        return False
