# AI图片搜索助手

基于Flet的Windows桌面图片搜索应用，支持OCR文字识别和语义搜索功能。

## 功能特点

- **文件夹选择**：浏览并选择包含图片的文件夹
- **两种搜索模式**：
  - 文字搜索（OCR）：通过OCR识别图片中的文字进行关键字搜索
  - 语义搜索：使用CLIP模型理解图片语义进行自然语言搜索
- **索引管理**：先建立索引再搜索，支持切换搜索模式后重新建立索引
- **图片预览**：点击搜索结果可查看大图预览

## 技术栈

- **UI框架**：Flet 0.84.0
- **OCR识别**：EasyOCR
- **语义搜索**：sentence-transformers (CLIP-ViT-B-32)
- **向量数据库**：FAISS

## 项目结构

```
aiSearch/
├── main.py                 # 应用入口
├── config.py               # 配置文件
├── cache/                  # 缓存目录
│   └── ocr_models/        # OCR模型文件
├── services/               # 服务层
│   ├── file_service.py     # 文件服务
│   ├── ocr_service.py      # OCR服务
│   ├── search_service.py   # 搜索服务
│   └── semantic_search_service.py  # 语义搜索服务
└── ui/                     # UI层
    ├── main_view.py        # 主视图
    ├── components.py        # UI组件
    └── constants.py         # 常量定义
```

## 使用方法

1. **启动应用**：运行 `python main.py`
2. **选择文件夹**：点击文件夹图标，选择包含图片的文件夹
3. **选择搜索模式**：
   - 点击"文字搜索"使用OCR识别
   - 点击"语义搜索"使用语义向量
4. **建立索引**：点击"建立索引"按钮，等待处理完成
5. **搜索图片**：在搜索框输入关键字，点击搜索按钮

## 搜索模式说明

### 文字搜索（OCR）

使用EasyOCR进行光学字符识别，可以从图片中提取文字信息。适用于搜索包含文字的图片，如截图、文档照片、书籍封面等。

### 语义搜索

使用CLIP模型将图片和文本映射到同一个向量空间，通过计算向量相似度进行匹配。适用于搜索概念性内容，如"猫"、"风景"、"日落"等。

### 模型安装
```bash
# 1. 安装 modelscope
pip install modelscope

# 2. 下载模型（以 v2 为例）
modelscope download jinaai/jina-clip-v2 --local_dir ./models/jina-clip-v2
```

## 运行要求

- Python 3.8+
- Windows操作系统
