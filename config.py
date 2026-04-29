"""
配置文件
"""
import os

# 项目根目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 支持的图片格式
IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff', '.webp'}

# 支持的视频格式
VIDEO_EXTENSIONS = {'.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm'}

# 支持的文档格式
DOCUMENT_EXTENSIONS = {'.pdf', '.doc', '.docx', '.txt', '.xls', '.xlsx', '.ppt', '.pptx'}

# 所有支持的文件格式
SUPPORTED_EXTENSIONS = IMAGE_EXTENSIONS | VIDEO_EXTENSIONS | DOCUMENT_EXTENSIONS

# 默认缓存目录
CACHE_DIR = os.path.join(BASE_DIR, 'cache')

# OCR模型缓存目录
OCR_MODEL_DIR = os.path.join(CACHE_DIR, 'ocr_models')

# 索引数据库目录
INDEX_DIR = os.path.join(CACHE_DIR, 'index')

# 语义搜索模型配置
SEMANTIC_MODEL_NAME = 'clip-ViT-B-32'
SEMANTIC_BATCH_SIZE = 32
SEMANTIC_TOP_K = 50
SEMANTIC_MODEL_PATH = './models/sentence-transformers/clip-ViT-B-32'

# 日志配置
LOG_LEVEL = 'INFO'
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

