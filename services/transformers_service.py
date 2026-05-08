"""
Transformers语义搜索服务模块 - 基于ChineseCLIP的语义搜索
"""
import os
import pickle
import numpy as np
from typing import List, Optional, Tuple

try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False
    print("Warning: FAISS not installed, semantic search will be limited")

from PIL import Image
import torch
from transformers import ChineseCLIPProcessor, ChineseCLIPModel
import traceback


class TransformersSearchService:
    """基于ChineseCLIP的语义搜索服务类"""

    def __init__(self, model_path: str = None):
        self.embedding_dim = 1024
        self.index: Optional[faiss.IndexFlatIP] = None
        self.image_files: List = []
        self.embeddings: Optional[np.ndarray] = None
        self._initialized = False
        self._model = None
        self._processor = None
        self._model_path = model_path

    def _load_model(self):
        """加载ChineseCLIP模型"""
        if self._model is not None:
            return

        try:
            model_path = self._model_path or "OFA-Sys/chinese-clip-vit-huge-patch14"

            print(f"正在加载ChineseCLIP模型: {model_path}")
            self._processor = ChineseCLIPProcessor.from_pretrained(model_path)
            self._model = ChineseCLIPModel.from_pretrained(model_path)

            device = 'cuda' if torch.cuda.is_available() else 'cpu'
            self._model.to(device)
            self._model.eval() # 切换到评估模式

            print(f"ChineseCLIP模型加载成功，设备: {device}")

        except Exception as e:
            print(f"加载ChineseCLIP模型失败: {e}")
            traceback.print_exc()
            raise

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

    def _extract_image_features(self, images: List[Image.Image]) -> np.ndarray:
        """批量提取图片特征"""
        inputs = self._processor(images=images, return_tensors="pt")
        inputs = {k: v.to(self._model.device) for k, v in inputs.items()}
        
        with torch.no_grad():
            outputs = self._model.get_image_features(**inputs)

            if hasattr(outputs, 'pooler_output'):
                image_embeds = outputs.pooler_output
            else:
                image_embeds = outputs

            image_embeds = image_embeds / image_embeds.norm(p=2, dim=-1, keepdim=True)
        
        return image_embeds.cpu().numpy().astype('float32')
    
    def _extract_text_features(self, texts: List[str]) -> np.ndarray:
        """提取文本特征"""
        text_inputs = self._processor(text=texts, return_tensors="pt", padding=True)
        text_inputs = {k: v.to(self._model.device) for k, v in text_inputs.items()}
        
        with torch.no_grad():
            outputs = self._model.get_text_features(**text_inputs)
            if hasattr(outputs, 'pooler_output'):
                text_embeds = outputs.pooler_output
            else:
                text_embeds = outputs
            text_embeds = text_embeds / text_embeds.norm(p=2, dim=-1, keepdim=True)
        
        return text_embeds.cpu().numpy().astype('float32')

    def create_image_embeddings(self, image_files: List, batch_size: int = 16) -> bool:
        """
        为图片文件创建向量embedding

        Args:
            image_files: 图片文件列表
            batch_size: 批处理大小

        Returns:
            是否成功
        """
        if not image_files:
            return False

        try:
            self._load_model()
            self.initialize()

            print(f"开始为 {len(image_files)} 张图片生成语义向量...")

            all_embeddings = []
            image_paths = [f.path for f in image_files]

            for i in range(0, len(image_paths), batch_size):
                batch_paths = image_paths[i:i + batch_size]
                batch_images = [Image.open(path) for path in batch_paths]

                image_embeds = self._extract_image_features(batch_images)
                all_embeddings.append(image_embeds)

                print(f"已处理 {min(i + batch_size, len(image_paths))}/{len(image_paths)} 张图片")

            embeddings = np.vstack(all_embeddings)
            self.embeddings = embeddings
            self.index.reset()
            self.index.add(self.embeddings)
            self.image_files = image_files

            print(f"语义向量创建完成，索引了 {len(image_files)} 张图片，向量维度: {self.embeddings.shape}")
            return True

        except Exception as e:
            print(f"创建图片语义向量失败: {e}")
            traceback.print_exc()
            return False

    def search_by_text(self, query_text: str, top_k: int = 10, min_similarity: float = 0.2) -> List[Tuple]:
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
            print("索引为空，无法进行搜索")
            return []

        if not query_text or not query_text.strip():
            results = []
            for i in range(min(top_k, self.index.ntotal)):
                results.append((self.image_files[i], 1.0))
            print(f"返回所有图片，共 {len(results)} 张")
            return results

        try:
            self._load_model()

            query_embedding = self._extract_text_features(query_text)
            distances, indices = self.index.search(query_embedding, min(top_k, self.index.ntotal))

            results = []
            print(f"调试 - 前5个原始距离: {[round(d, 4) for d in distances[0][:5]]}")
            for dist, idx in zip(distances[0], indices[0]):
                if idx >= 0 and idx < len(self.image_files):
                    if dist >= min_similarity:
                        results.append((self.image_files[idx], float(dist)))

            print(f"语义搜索完成，返回 {len(results)} 个结果（阈值: {min_similarity}）")

            return results

        except Exception as e:
            print(f"语义搜索失败: {e}")            
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
                'files': self.image_files,
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

    def release_model(self):
        """释放模型资源"""
        if self._model is not None:
            del self._model
            del self._processor
            self._model = None
            self._processor = None
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            print("ChineseCLIP模型已释放")