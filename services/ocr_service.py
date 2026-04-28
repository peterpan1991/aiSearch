"""
OCR服务模块 - 图片文字识别
"""
import easyocr
from PIL import Image
import numpy as np
import cv2
from typing import List, Callable, Optional
import config

class OCRService:
    """OCR服务类"""

    def __init__(self):
        self.reader: Optional[easyocr.Reader] = None
        self.initialized = False
        self.image_cache: List = []

    def initialize(self):
        """初始化OCR reader"""
        if not self.initialized:
            self.reader = easyocr.Reader(
                ['ch_sim', 'en'],
                model_storage_directory=config.OCR_MODEL_DIR,
                download_enabled=True,
                gpu=False
            )
            self.initialized = True

    def _read_image_with_chinese_path(self, image_path: str) -> Optional[np.ndarray]:
        """
        读取图片，支持中文路径

        Args:
            image_path: 图片路径

        Returns:
            numpy array格式的图片数据，失败返回None
        """
        try:
            # 方法1：用Pillow读取中文路径
            img = Image.open(image_path)
            img_array = np.array(img)

            # 转换为BGR格式（OpenCV格式）
            if len(img_array.shape) == 3 and img_array.shape[2] == 3:
                # RGB to BGR
                img_bgr = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
                return img_bgr
            return img_array

        except Exception as e:
            print(f"图片读取失败 {image_path}: {e}")
            return None

    def process_images(self, image_files: List, progress_callback: Optional[Callable] = None):
        """
        处理图片列表，进行OCR识别

        Args:
            image_files: 图片文件列表
            progress_callback: 进度回调函数(current, total, filename)
        """

        print("开始初始化OCR reader")
        self.initialize()

        print(f"开始处理 {len(image_files)} 张图片")

        for idx, file_item in enumerate(image_files):
            try:
                # 进度回调
                if progress_callback:
                    progress_callback(idx + 1, len(image_files), file_item.name)

                print(f"正在处理 {file_item.path}")

                # 使用支持中文路径的方式读取图片
                img_array = self._read_image_with_chinese_path(file_item.path)

                if img_array is not None:
                    # 执行OCR识别
                    result = self.reader.readtext(img_array)

                    # 提取文本
                    text_parts = []
                    for detection in result:
                        text_parts.append(detection[1])

                    file_item.ocr_text = " ".join(text_parts)
                else:
                    file_item.ocr_text = ""

            except Exception as e:
                print(f"OCR处理失败 {file_item.path}: {e}")
                file_item.ocr_text = ""

            # 缓存结果
            self.image_cache.append(file_item)

    def search(self, keyword: str) -> List:
        """
        搜索包含关键字的图片

        Args:
            keyword: 搜索关键字

        Returns:
            匹配的文件列表
        """
        print(f"开始搜索关键字: {keyword}")
        if not keyword:
            return self.image_cache

        keyword_lower = keyword.lower()
        results = []

        for file_item in self.image_cache:
            if file_item.matches_keyword(keyword_lower):
                results.append(file_item)

        return results

    def get_all_processed_images(self) -> List:
        """获取所有已处理的图片"""
        return self.image_cache

    def clear_cache(self):
        """清空缓存"""
        self.image_cache.clear()
