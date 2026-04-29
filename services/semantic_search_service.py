"""
语义搜索服务模块 - 基于向量相似度的语义搜索
"""
import os
import pickle
import numpy as np
from typing import List, Optional, Tuple
import config

try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False
    print("Warning: FAISS not installed, semantic search will be limited")


class SemanticSearchService:
    """语义搜索服务类"""

    def __init__(self):
        self.embedding_dim = 512
        self.index: Optional[faiss.IndexFlatIP] = None
        self.image_files: List = []
        self.embeddings: Optional[np.ndarray] = None
        self._initialized = False

    def initialize(self):
        """初始化向量索引"""
        if not FAISS_AVAILABLE:
            print("FAISS not available, semantic search disabled")
            return

        if not self._initialized:
            self.index = faiss.IndexFlatIP(self.embedding_dim)
            self._initialized = True

    def _normalize_embeddings(self, embeddings: np.ndarray) -> np.ndarray:
        """归一化向量用于余弦相似度"""
        if embeddings.ndim == 1:
            norm = np.linalg.norm(embeddings)
            if norm == 0:
                return embeddings.reshape(1, -1) if embeddings.shape[0] > 0 else embeddings
            return (embeddings / norm).reshape(1, -1)
        else:
            norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
            norms = np.where(norms == 0, 1, norms)
            return embeddings / norms

    def create_image_embeddings(self, image_files: List) -> bool:
        """
        为图片文件创建向量embedding

        Args:
            image_files: 图片文件列表

        Returns:
            是否成功
        """
        if not FAISS_AVAILABLE or not image_files:
            return False

        try:
            from sentence_transformers import SentenceTransformer
            from PIL import Image
            import torch

            self.initialize()

            print(f"开始为 {len(image_files)} 张图片生成语义向量...")

            model = SentenceTransformer(config.SEMANTIC_MODEL_PATH, local_files_only=True)
            device = 'cuda' if torch.cuda.is_available() else 'cpu'
            model.to(device)

            image_paths = [f.path for f in image_files]

            images = [Image.open(path).convert('RGB') for path in image_paths]
            embeddings = model.encode(images, batch_size=32, convert_to_numpy=True, show_progress_bar=True)

            self.embeddings = self._normalize_embeddings(embeddings).astype('float32')
            self.index.reset()
            self.index.add(self.embeddings)
            self.image_files = image_files

            print(f"语义向量创建完成，索引了 {len(image_files)} 张图片，向量维度: {self.embeddings.shape}")
            return True

        except Exception as e:
            print(f"创建图片语义向量失败: {e}")
            import traceback
            traceback.print_exc()
            return False

    def search_by_text(self, query_text: str, top_k: int = 10, min_similarity: float = 0.25) -> List[Tuple]:
        """
        通过文本搜索相似图片

        Args:
            query_text: 查询文本
            top_k: 返回结果数量
            min_similarity: 最小相似度阈值，低于此值的结果将被过滤

        Returns:
            [(FileItem, distance), ...] 列表
        """
        if not self.index or self.index.ntotal == 0:
            return []

        try:
            print(f"开始语义搜索: {query_text}")
            from sentence_transformers import SentenceTransformer
            import torch

            model = SentenceTransformer(config.SEMANTIC_MODEL_PATH, local_files_only=True)
            device = 'cuda' if torch.cuda.is_available() else 'cpu'
            model.to(device)

            query_embedding = model.encode(query_text).astype('float32')
            query_embedding = self._normalize_embeddings(query_embedding)
            distances, indices = self.index.search(query_embedding, min(top_k, self.index.ntotal))

            results = []
            for dist, idx in zip(distances[0], indices[0]):
                if idx >= 0 and idx < len(self.image_files) and dist >= min_similarity:
                    results.append((self.image_files[idx], float(dist)))

            print(f"语义搜索完成，返回 {len(results)} 个结果（阈值: {min_similarity}）")

            return results

        except Exception as e:
            print(f"语义搜索失败: {e}")
            import traceback
            traceback.print_exc()
            return []

    def save_index(self, save_path: str):
        """保存索引到文件"""
        if not self.index or self.index.ntotal == 0:
            return

        try:
            os.makedirs(os.path.dirname(save_path), exist_ok=True)

            index_data = {
                'index': faiss.serialize_index(self.index),
                'files': [f.path for f in self.image_files],
                'embeddings': self.embeddings,
            }

            with open(save_path, 'wb') as f:
                pickle.dump(index_data, f)

            print(f"索引已保存到: {save_path}")
        except Exception as e:
            print(f"保存索引失败: {e}")

    def load_index(self, load_path: str) -> bool:
        """从文件加载索引"""
        if not os.path.exists(load_path):
            return False

        try:
            with open(load_path, 'rb') as f:
                index_data = pickle.load(f)

            self.index = faiss.deserialize_index(index_data['index'])
            self.image_files = index_data['files']
            self.embeddings = index_data['embeddings']

            print(f"索引已加载，共 {len(self.image_files)} 张图片")
            return True

        except Exception as e:
            print(f"加载索引失败: {e}")
            return False

    def clear(self):
        """清空索引"""
        if self.index:
            self.index.reset()
        self.image_files.clear()
        self.embeddings = None
