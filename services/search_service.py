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
        self.current_mode = SearchMode.SEMANTIC
        self.index_built = False
        self._image_folder = None

    def is_index_built(self) -> bool:
        """检查索引是否已建立"""
        return self.index_built

    def load_cached_index(self, image_folder: str) -> bool:
        """
        尝试加载缓存的索引

        Args:
            image_folder: 图片文件夹路径

        Returns:
            是否成功加载索引
        """
        self._image_folder = image_folder
        
        if self.current_mode == SearchMode.SEMANTIC:
            return self._load_semantic_index()
        elif self.current_mode == SearchMode.OCR:
            return self._load_ocr_index()
        return False

    def _load_semantic_index(self) -> bool:
        """加载语义索引缓存"""
        import os
        if not os.path.exists(config.SEMANTIC_INDEX_CACHE):
            return False

        try:
            self.initialize_semantic()
            loaded = self.semantic_service.load_index(config.SEMANTIC_INDEX_CACHE)
            if loaded:
                self.index_built = True
                print("已加载缓存的语义索引")
                return True
        except Exception as e:
            print(f"加载语义索引缓存失败: {e}")
        return False

    def _load_ocr_index(self) -> bool:
        """加载OCR索引缓存"""
        import os
        if not os.path.exists(config.OCR_INDEX_CACHE):
            return False

        try:
            self.initialize_ocr()
            loaded = self.ocr_service.load_index(config.OCR_INDEX_CACHE)
            if loaded:
                self.index_built = True
                print("已加载缓存的OCR索引")
                return True
        except Exception as e:
            print(f"加载OCR索引缓存失败: {e}")
        return False

    def reset_index_status(self):
        """重置索引状态"""
        self.index_built = False

    def set_mode(self, mode: SearchMode):
        """设置搜索模式"""
        self.current_mode = mode

    def initialize_ocr(self):
        """初始化OCR服务"""
        if self.ocr_service is None:
            from services.ocr_service import OCRService
            self.ocr_service = OCRService()

    def initialize_semantic(self):
        """初始化语义搜索服务"""
        if self.semantic_service is None:
            from services.transformers_service import TransformersSearchService
            self.semantic_service = TransformersSearchService(model_path='./models/OFA-Sys/chinese-clip-vit-huge-patch14')

    def process_images(self, image_files: List[FileItem], progress_callback=None):
        """
        处理图片 - 根据当前模式生成OCR文本或语义向量

        Args:
            image_files: 图片文件列表
            progress_callback: 进度回调
        """
        if not image_files:
            return

        if self.current_mode == SearchMode.OCR:
            self._process_ocr(image_files, progress_callback)
        elif self.current_mode == SearchMode.SEMANTIC:
            self._process_semantic(image_files, progress_callback)

    def _process_ocr(self, image_files: List[FileItem], progress_callback):
        """处理OCR"""
        self.initialize_ocr()
        self.ocr_service.process_images(image_files, progress_callback)
        self.index_built = True
        self._save_ocr_index()

    def _save_ocr_index(self):
        """保存OCR索引到缓存"""
        try:
            import os
            os.makedirs(os.path.dirname(config.OCR_INDEX_CACHE), exist_ok=True)
            self.ocr_service.save_index(config.OCR_INDEX_CACHE)
        except Exception as e:
            print(f"保存OCR索引失败: {e}")

    def _process_semantic(self, image_files: List[FileItem], progress_callback):
        """处理语义向量"""
        self.initialize_semantic()

        def semantic_progress_wrapper(current, total, filename):
            if progress_callback:
                progress_callback(current + total, total * 2, f"生成语义向量: {filename}")

        self.semantic_service.create_image_embeddings(image_files)
        self.index_built = True
        self._save_semantic_index()

    def _save_semantic_index(self):
        """保存语义索引到缓存"""
        try:
            import os
            os.makedirs(os.path.dirname(config.SEMANTIC_INDEX_CACHE), exist_ok=True)
            self.semantic_service.save_index(config.SEMANTIC_INDEX_CACHE)
        except Exception as e:
            print(f"保存语义索引失败: {e}")

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
        # if not query:
        #     return []

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
        print(f"开始语义搜索: {query}")
        self.initialize_semantic()
        results = self.semantic_service.search_by_text(query, top_k)
        items = []
        for item, similarity in results:
            item.similarity = similarity
            items.append(item)
        return items

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
