"""
基于文件的向量存储实现 - 无需数据库
适用于只有文档的场景
"""
import json
import os
import pickle
from pathlib import Path
from typing import List, Dict, Optional
from langchain_core.embeddings import Embeddings
import jieba
from .vector_store import SearchMode, BaseVectorStore, text_to_chunk


class FileVectorStore(BaseVectorStore):
    """基于文件的向量存储实现"""
    
    def __init__(self, storage_path: str = "./rag_storage"):
        """
        初始化文件向量存储
        :param storage_path: 存储路径
        """
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # 存储文件路径
        self.vectors_file = self.storage_path / "vectors.pkl"
        self.metadata_file = self.storage_path / "metadata.json"
        
        # 内存中的数据结构
        self.vectors: Dict[str, List[float]] = {}  # paragraph_id -> embedding
        self.metadata: Dict[str, Dict] = {}  # paragraph_id -> metadata
        
        # 加载已有数据
        self._load_data()
    
    def _load_data(self):
        """加载已有数据"""
        try:
            if self.vectors_file.exists():
                with open(self.vectors_file, 'rb') as f:
                    self.vectors = pickle.load(f)
            
            if self.metadata_file.exists():
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    self.metadata = json.load(f)
        except Exception as e:
            print(f"加载数据失败: {e}")
            self.vectors = {}
            self.metadata = {}
    
    def _save_data(self):
        """保存数据到文件"""
        try:
            with open(self.vectors_file, 'wb') as f:
                pickle.dump(self.vectors, f)
            
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(self.metadata, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存数据失败: {e}")
    
    def save(self, text: str, knowledge_id: str, document_id: str,
             paragraph_id: str, embedding: Embeddings, **kwargs):
        """保存单个向量"""
        # 向量化文本
        text_embedding = embedding.embed_query(text)
        
        # 存储向量
        self.vectors[paragraph_id] = text_embedding
        
        # 存储元数据
        self.metadata[paragraph_id] = {
            'text': text,
            'knowledge_id': knowledge_id,
            'document_id': document_id,
            'paragraph_id': paragraph_id,
            'source_id': kwargs.get('source_id', paragraph_id),
            'source_type': kwargs.get('source_type', '1'),
            'is_active': kwargs.get('is_active', True),
            'meta': kwargs.get('meta', {})
        }
        
        self._save_data()
    
    def batch_save(self, data_list: List[Dict], embedding: Embeddings):
        """批量保存向量"""
        if not data_list:
            return
        
        # 批量向量化
        texts = [item['text'] for item in data_list]
        embeddings = embedding.embed_documents(texts)
        
        for idx, item in enumerate(data_list):
            paragraph_id = item.get('paragraph_id', f"para_{idx}")
            self.vectors[paragraph_id] = embeddings[idx]
            self.metadata[paragraph_id] = {
                'text': item['text'],
                'knowledge_id': item.get('knowledge_id'),
                'document_id': item.get('document_id'),
                'paragraph_id': paragraph_id,
                'source_id': item.get('source_id', paragraph_id),
                'source_type': item.get('source_type', '1'),
                'is_active': item.get('is_active', True),
                'meta': item.get('meta', {})
            }
        
        self._save_data()
    
    def search(self, query_text: str, knowledge_id_list: List[str],
               top_n: int = 5, similarity: float = 0.7,
               search_mode: SearchMode = SearchMode.EMBEDDING,
               embedding: Embeddings = None) -> List[Dict]:
        """检索向量"""
        if not knowledge_id_list:
            return []
        
        if search_mode == SearchMode.EMBEDDING and embedding is None:
            raise ValueError("embedding 参数在 EMBEDDING 模式下是必需的")
        
        results = []
        
        # 过滤出指定知识库的段落
        candidate_paragraphs = [
            pid for pid, meta in self.metadata.items()
            if meta.get('knowledge_id') in knowledge_id_list and meta.get('is_active', True)
        ]
        
        if search_mode == SearchMode.EMBEDDING:
            results = self._embedding_search(query_text, candidate_paragraphs, embedding, top_n, similarity)
        elif search_mode == SearchMode.KEYWORDS:
            results = self._keywords_search(query_text, candidate_paragraphs, top_n, similarity)
        elif search_mode == SearchMode.BLEND:
            results = self._blend_search(query_text, candidate_paragraphs, embedding, top_n, similarity)
        
        return results
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """计算余弦相似度"""
        import math
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        magnitude1 = math.sqrt(sum(a * a for a in vec1))
        magnitude2 = math.sqrt(sum(a * a for a in vec2))
        
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0
        
        return dot_product / (magnitude1 * magnitude2)
    
    def _embedding_search(self, query_text: str, candidate_paragraphs: List[str],
                         embedding: Embeddings, top_n: int, similarity: float) -> List[Dict]:
        """向量检索"""
        query_embedding = embedding.embed_query(query_text)
        
        scores = []
        for paragraph_id in candidate_paragraphs:
            if paragraph_id not in self.vectors:
                continue
            
            para_embedding = self.vectors[paragraph_id]
            sim = self._cosine_similarity(query_embedding, para_embedding)
            
            if sim >= similarity:
                meta = self.metadata[paragraph_id]
                scores.append({
                    'paragraph_id': paragraph_id,
                    'similarity': sim,
                    'comprehensive_score': sim,
                    'knowledge_id': meta.get('knowledge_id'),
                    'document_id': meta.get('document_id'),
                    'source_id': meta.get('source_id'),
                    'source_type': meta.get('source_type'),
                    'text': meta.get('text', '')
                })
        
        # 按相似度排序
        scores.sort(key=lambda x: x['similarity'], reverse=True)
        return scores[:top_n]
    
    def _keywords_search(self, query_text: str, candidate_paragraphs: List[str],
                        top_n: int, similarity: float) -> List[Dict]:
        """关键词检索"""
        query_keywords = set(jieba.lcut(query_text))
        
        scores = []
        for paragraph_id in candidate_paragraphs:
            if paragraph_id not in self.metadata:
                continue
            
            meta = self.metadata[paragraph_id]
            text = meta.get('text', '')
            text_keywords = set(jieba.lcut(text))
            
            # 计算关键词匹配度
            if query_keywords:
                match_count = len(query_keywords & text_keywords)
                sim = match_count / len(query_keywords)
            else:
                sim = 0.0
            
            if sim >= similarity:
                scores.append({
                    'paragraph_id': paragraph_id,
                    'similarity': sim,
                    'comprehensive_score': sim,
                    'knowledge_id': meta.get('knowledge_id'),
                    'document_id': meta.get('document_id'),
                    'source_id': meta.get('source_id'),
                    'source_type': meta.get('source_type'),
                    'text': text
                })
        
        # 按相似度排序
        scores.sort(key=lambda x: x['similarity'], reverse=True)
        return scores[:top_n]
    
    def _blend_search(self, query_text: str, candidate_paragraphs: List[str],
                     embedding: Embeddings, top_n: int, similarity: float) -> List[Dict]:
        """混合检索"""
        query_embedding = embedding.embed_query(query_text)
        query_keywords = set(jieba.lcut(query_text))
        
        scores = []
        for paragraph_id in candidate_paragraphs:
            if paragraph_id not in self.vectors or paragraph_id not in self.metadata:
                continue
            
            # 向量相似度
            para_embedding = self.vectors[paragraph_id]
            embedding_sim = self._cosine_similarity(query_embedding, para_embedding)
            
            # 关键词相似度
            meta = self.metadata[paragraph_id]
            text = meta.get('text', '')
            text_keywords = set(jieba.lcut(text))
            if query_keywords:
                keyword_sim = len(query_keywords & text_keywords) / len(query_keywords)
            else:
                keyword_sim = 0.0
            
            # 混合分数
            sim = (embedding_sim + keyword_sim) / 2
            
            if sim >= similarity:
                scores.append({
                    'paragraph_id': paragraph_id,
                    'similarity': sim,
                    'comprehensive_score': sim,
                    'knowledge_id': meta.get('knowledge_id'),
                    'document_id': meta.get('document_id'),
                    'source_id': meta.get('source_id'),
                    'source_type': meta.get('source_type'),
                    'text': text
                })
        
        # 按相似度排序
        scores.sort(key=lambda x: x['similarity'], reverse=True)
        return scores[:top_n]
    
    def delete_by_knowledge_id(self, knowledge_id: str):
        """删除知识库的所有向量"""
        to_delete = [
            pid for pid, meta in self.metadata.items()
            if meta.get('knowledge_id') == knowledge_id
        ]
        for pid in to_delete:
            self.vectors.pop(pid, None)
            self.metadata.pop(pid, None)
        self._save_data()
    
    def delete_by_document_id(self, document_id: str):
        """删除文档的所有向量"""
        to_delete = [
            pid for pid, meta in self.metadata.items()
            if meta.get('document_id') == document_id
        ]
        for pid in to_delete:
            self.vectors.pop(pid, None)
            self.metadata.pop(pid, None)
        self._save_data()
    
    def delete_by_paragraph_id(self, paragraph_id: str):
        """删除段落的向量"""
        self.vectors.pop(paragraph_id, None)
        self.metadata.pop(paragraph_id, None)
        self._save_data()

