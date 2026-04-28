"""
搜索服务模块 - 统一管理OCR搜索和语义搜索
"""
from typing import List, Tuple, Optional
from enum import Enum
import config
from models.file_item import FileItem


class SearchMode(Enum):
    """搜索模式"""
    OCR = "ocr"
    SEMANTIC = "semantic"


class SearchService:
    """搜索服务类 - 统一管理OCR和语义搜索"""

    def __init__(self):
        self.ocr_service = None
        self.semantic_service = None
        self.current_mode = SearchMode.OCR

    def initialize_ocr(self):
        """初始化OCR服务"""
        if self.ocr_service is None:
            from services.ocr_service import OCRService
            self.ocr_service = OCRService()

    def initialize_semantic(self):
        """初始化语义搜索服务"""
        if self.semantic_service is None:
            from services.semantic_search_service import SemanticSearchService
            self.semantic_service = SemanticSearchService()

    def process_images(self, image_files: List[FileItem], progress_callback=None):
        """
        处理图片 - 同时生成OCR文本和语义向量

        Args:
            image_files: 图片文件列表
            progress_callback: 进度回调
        """
        if not image_files:
            return

        self.initialize_ocr()
        # self.initialize_semantic()

        self.ocr_service.process_images(image_files, progress_callback)

        # def semantic_progress(current, total, filename):
        #     if progress_callback:
        #         progress_callback(current + total, total * 2, f"生成语义向量: {filename}")

        # self.semantic_service.create_image_embeddings(image_files)

    def search(self, query: str, mode: SearchMode = SearchMode.OCR, top_k: int = 50) -> List[FileItem]:
        """
        执行搜索

        Args:
            query: 搜索查询
            mode: 搜索模式
            top_k: 返回结果数量

        Returns:
            匹配的文件列表
        """
        if not query:
            return []

        if mode == SearchMode.OCR:
            return self._ocr_search(query)
        elif mode == SearchMode.SEMANTIC:
            return self._semantic_search(query, top_k)
        else:
            return []

    def _ocr_search(self, query: str) -> List[FileItem]:
        """OCR搜索 - 关键字匹配"""
        self.initialize_ocr()
        results = self.ocr_service.search(query)
        return results

    def _semantic_search(self, query: str, top_k: int) -> List[FileItem]:
        """语义搜索 - 向量相似度"""
        self.initialize_semantic()
        results = self.semantic_service.search_by_text(query, top_k)
        return [item for item, _ in results]

    def clear_cache(self):
        """清空缓存"""
        if self.ocr_service:
            self.ocr_service.clear_cache()
        if self.semantic_service:
            self.semantic_service.clear()

    def get_all_processed_images(self) -> List[FileItem]:
        """获取所有已处理的图片"""
        if self.ocr_service:
            return self.ocr_service.get_all_processed_images()
        return []
