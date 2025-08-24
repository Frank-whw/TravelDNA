#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RAG增强检索系统
为上海旅游AI提供智能知识检索能力
集成传统检索和向量检索，支持MCP服务
"""

import os
import json
import re
import jieba
import numpy as np
from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime
import logging
from collections import defaultdict, Counter
from dataclasses import dataclass
import pickle

# 尝试导入向量检索相关库
try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    print("Warning: sentence-transformers not available, falling back to traditional retrieval")

try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False
    print("Warning: faiss not available, using simple similarity search")

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class RetrievalResult:
    """检索结果数据类"""
    doc_id: str
    title: str
    content: str
    score: float
    doc_type: str
    metadata: Dict[str, Any]
    retrieval_method: str

class TraditionalRetriever:
    """传统关键词检索器"""
    
    def __init__(self, data_dir: str = "./data"):
        self.data_dir = data_dir
        self.documents = []
        self.doc_index = {}
        self.keyword_index = defaultdict(set)
        self.idf_scores = {}
        
        # 加载停用词
        self.stopwords = self._load_stopwords()
        
        # 初始化jieba分词
        jieba.setLogLevel(logging.WARNING)
        self._load_custom_dict()
    
    def _load_stopwords(self) -> set:
        """加载停用词"""
        stopwords = {
            '的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一', '一个', '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好', '自己', '这', '那', '可以', '什么', '比较', '还是', '里', '面', '用', '来', '最', '大', '小', '多', '少', '高', '低', '新', '旧', '长', '短', '快', '慢'
        }
        
        # 旅游相关停用词
        tourism_stopwords = {
            '景点', '地方', '这里', '那里', '地址', '位置', '时间', '门票', '价格', '游客', '旅游', '参观', '游览', '推荐'
        }
        
        return stopwords | tourism_stopwords
    
    def _load_custom_dict(self):
        """加载自定义词典"""
        custom_words = [
            '外滩', '东方明珠', '豫园', '城隍庙', '南京路', '新天地', '田子坊',
            '朱家角', '七宝古镇', '上海博物馆', '上海科技馆', '迪士尼乐园',
            '野生动物园', '植物园', '中山公园', '人民广场', '陆家嘴', '静安寺',
            '黄浦江', '苏州河', '世博园', '上海大剧院', '环球金融中心', '金茂大厦',
            '上海中心', '淮海路', '四川北路', '多伦路', '鲁迅公园', '复兴公园'
        ]
        
        for word in custom_words:
            jieba.add_word(word)
    
    def load_documents(self, corpus_file: str = None) -> int:
        """加载文档语料库"""
        if not corpus_file:
            corpus_file = f"{self.data_dir}/rag_corpus/shanghai_tourism_corpus.json"
        
        if not os.path.exists(corpus_file):
            logger.warning(f"语料库文件不存在: {corpus_file}")
            return 0
        
        try:
            with open(corpus_file, 'r', encoding='utf-8') as f:
                corpus_data = json.load(f)
            
            self.documents = corpus_data
            self._build_index()
            
            logger.info(f"加载文档成功: {len(self.documents)}个文档")
            return len(self.documents)
            
        except Exception as e:
            logger.error(f"加载文档失败: {e}")
            return 0
    
    def _build_index(self):
        """构建倒排索引"""
        doc_word_counts = []
        total_docs = len(self.documents)
        
        for i, doc in enumerate(self.documents):
            self.doc_index[doc['id']] = i
            
            # 合并标题和内容
            text = f"{doc.get('title', '')} {doc.get('content', '')}"
            words = self._tokenize(text)
            
            # 统计词频
            word_counts = Counter(words)
            doc_word_counts.append(word_counts)
            
            # 建立倒排索引
            for word in set(words):
                self.keyword_index[word].add(i)
        
        # 计算IDF分数
        for word, doc_indices in self.keyword_index.items():
            df = len(doc_indices)  # 文档频率
            self.idf_scores[word] = np.log(total_docs / (df + 1))
        
        logger.info(f"索引构建完成: {len(self.keyword_index)}个词条")
    
    def _tokenize(self, text: str) -> List[str]:
        """分词处理"""
        if not text:
            return []
        
        # 使用jieba分词
        words = jieba.lcut(text.lower())
        
        # 过滤停用词和短词
        filtered_words = [
            word.strip() for word in words 
            if len(word.strip()) > 1 and word.strip() not in self.stopwords
        ]
        
        return filtered_words
    
    def search(self, query: str, top_k: int = 5) -> List[RetrievalResult]:
        """关键词搜索"""
        if not self.documents:
            return []
        
        query_words = self._tokenize(query)
        if not query_words:
            return []
        
        # 计算文档分数
        doc_scores = defaultdict(float)
        
        for word in query_words:
            if word in self.keyword_index:
                idf = self.idf_scores.get(word, 0)
                
                for doc_idx in self.keyword_index[word]:
                    # TF-IDF评分
                    doc = self.documents[doc_idx]
                    text = f"{doc.get('title', '')} {doc.get('content', '')}"
                    tf = text.lower().count(word) / max(len(self._tokenize(text)), 1)
                    doc_scores[doc_idx] += tf * idf
        
        # 排序并返回top_k结果
        ranked_docs = sorted(doc_scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
        
        results = []
        for doc_idx, score in ranked_docs:
            doc = self.documents[doc_idx]
            result = RetrievalResult(
                doc_id=doc['id'],
                title=doc.get('title', ''),
                content=doc.get('content', ''),
                score=score,
                doc_type=doc.get('type', ''),
                metadata=doc.get('metadata', {}),
                retrieval_method='keyword'
            )
            results.append(result)
        
        return results
    
    def fuzzy_search(self, query: str, top_k: int = 5) -> List[RetrievalResult]:
        """模糊搜索"""
        if not self.documents:
            return []
        
        # 简单的字符串相似度搜索
        doc_scores = []
        
        for i, doc in enumerate(self.documents):
            text = f"{doc.get('title', '')} {doc.get('content', '')}"
            
            # 计算包含度分数
            score = 0
            for char in query:
                if char in text:
                    score += 1
            
            # 长度归一化
            if len(text) > 0:
                score = score / len(query) * 100
            
            if score > 0:
                doc_scores.append((i, score))
        
        # 排序并返回结果
        ranked_docs = sorted(doc_scores, key=lambda x: x[1], reverse=True)[:top_k]
        
        results = []
        for doc_idx, score in ranked_docs:
            doc = self.documents[doc_idx]
            result = RetrievalResult(
                doc_id=doc['id'],
                title=doc.get('title', ''),
                content=doc.get('content', ''),
                score=score,
                doc_type=doc.get('type', ''),
                metadata=doc.get('metadata', {}),
                retrieval_method='fuzzy'
            )
            results.append(result)
        
        return results

class VectorRetriever:
    """向量检索器"""
    
    def __init__(self, data_dir: str = "./data", model_name: str = "all-MiniLM-L6-v2"):
        self.data_dir = data_dir
        self.model_name = model_name
        self.model = None
        self.documents = []
        self.embeddings = None
        self.index = None
        
        if SENTENCE_TRANSFORMERS_AVAILABLE:
            try:
                self.model = SentenceTransformer(model_name)
                logger.info(f"向量模型加载成功: {model_name}")
            except Exception as e:
                logger.warning(f"向量模型加载失败: {e}")
                self.model = None
        
    def load_documents(self, corpus_file: str = None) -> int:
        """加载文档并构建向量索引"""
        if not self.model:
            logger.warning("向量模型不可用，跳过向量索引构建")
            return 0
        
        if not corpus_file:
            corpus_file = f"{self.data_dir}/rag_corpus/shanghai_tourism_corpus.json"
        
        if not os.path.exists(corpus_file):
            logger.warning(f"语料库文件不存在: {corpus_file}")
            return 0
        
        try:
            with open(corpus_file, 'r', encoding='utf-8') as f:
                corpus_data = json.load(f)
            
            self.documents = corpus_data
            
            # 构建向量索引
            texts = []
            for doc in self.documents:
                # 合并标题和内容
                text = f"{doc.get('title', '')} {doc.get('content', '')}"
                texts.append(text)
            
            # 生成嵌入向量
            logger.info("正在生成文档向量...")
            self.embeddings = self.model.encode(texts, show_progress_bar=True)
            
            # 构建FAISS索引（如果可用）
            if FAISS_AVAILABLE:
                dimension = self.embeddings.shape[1]
                self.index = faiss.IndexFlatIP(dimension)  # 内积相似度
                # 归一化向量
                faiss.normalize_L2(self.embeddings)
                self.index.add(self.embeddings.astype('float32'))
                logger.info("FAISS索引构建完成")
            
            # 保存向量索引
            self._save_index()
            
            logger.info(f"向量索引构建成功: {len(self.documents)}个文档")
            return len(self.documents)
            
        except Exception as e:
            logger.error(f"构建向量索引失败: {e}")
            return 0
    
    def _save_index(self):
        """保存向量索引"""
        try:
            index_dir = f"{self.data_dir}/rag_corpus/vector_index"
            os.makedirs(index_dir, exist_ok=True)
            
            # 保存embeddings
            np.save(f"{index_dir}/embeddings.npy", self.embeddings)
            
            # 保存文档映射
            with open(f"{index_dir}/doc_mapping.json", 'w', encoding='utf-8') as f:
                doc_mapping = [
                    {'id': doc['id'], 'title': doc.get('title', ''), 'type': doc.get('type', '')}
                    for doc in self.documents
                ]
                json.dump(doc_mapping, f, ensure_ascii=False, indent=2)
            
            # 保存FAISS索引
            if self.index:
                faiss.write_index(self.index, f"{index_dir}/faiss.index")
            
            logger.info("向量索引保存成功")
            
        except Exception as e:
            logger.error(f"保存向量索引失败: {e}")
    
    def load_index(self) -> bool:
        """加载预构建的向量索引"""
        try:
            index_dir = f"{self.data_dir}/rag_corpus/vector_index"
            
            if not os.path.exists(f"{index_dir}/embeddings.npy"):
                return False
            
            # 加载embeddings
            self.embeddings = np.load(f"{index_dir}/embeddings.npy")
            
            # 加载文档映射
            with open(f"{index_dir}/doc_mapping.json", 'r', encoding='utf-8') as f:
                doc_mapping = json.load(f)
            
            # 重新加载完整文档信息
            corpus_file = f"{self.data_dir}/rag_corpus/shanghai_tourism_corpus.json"
            if os.path.exists(corpus_file):
                with open(corpus_file, 'r', encoding='utf-8') as f:
                    self.documents = json.load(f)
            
            # 加载FAISS索引
            if FAISS_AVAILABLE and os.path.exists(f"{index_dir}/faiss.index"):
                self.index = faiss.read_index(f"{index_dir}/faiss.index")
            
            logger.info("向量索引加载成功")
            return True
            
        except Exception as e:
            logger.error(f"加载向量索引失败: {e}")
            return False
    
    def search(self, query: str, top_k: int = 5) -> List[RetrievalResult]:
        """向量相似度搜索"""
        if not self.model or self.embeddings is None:
            return []
        
        try:
            # 生成查询向量
            query_embedding = self.model.encode([query])
            
            if self.index:
                # 使用FAISS搜索
                faiss.normalize_L2(query_embedding)
                scores, indices = self.index.search(query_embedding.astype('float32'), top_k)
                
                results = []
                for i, (score, idx) in enumerate(zip(scores[0], indices[0])):
                    if idx < len(self.documents):
                        doc = self.documents[idx]
                        result = RetrievalResult(
                            doc_id=doc['id'],
                            title=doc.get('title', ''),
                            content=doc.get('content', ''),
                            score=float(score),
                            doc_type=doc.get('type', ''),
                            metadata=doc.get('metadata', {}),
                            retrieval_method='vector_faiss'
                        )
                        results.append(result)
                
                return results
            
            else:
                # 简单余弦相似度搜索
                from sklearn.metrics.pairwise import cosine_similarity
                
                similarities = cosine_similarity(query_embedding, self.embeddings)[0]
                top_indices = np.argsort(similarities)[::-1][:top_k]
                
                results = []
                for idx in top_indices:
                    doc = self.documents[idx]
                    result = RetrievalResult(
                        doc_id=doc['id'],
                        title=doc.get('title', ''),
                        content=doc.get('content', ''),
                        score=float(similarities[idx]),
                        doc_type=doc.get('type', ''),
                        metadata=doc.get('metadata', {}),
                        retrieval_method='vector_cosine'
                    )
                    results.append(result)
                
                return results
        
        except Exception as e:
            logger.error(f"向量搜索失败: {e}")
            return []

class HybridRAGRetriever:
    """混合RAG检索器"""
    
    def __init__(self, data_dir: str = "./data"):
        self.data_dir = data_dir
        
        # 初始化检索器
        self.traditional_retriever = TraditionalRetriever(data_dir)
        self.vector_retriever = VectorRetriever(data_dir) if SENTENCE_TRANSFORMERS_AVAILABLE else None
        
        self.is_loaded = False
        
        # 权重配置
        self.retrieval_weights = {
            'keyword': 0.4,
            'vector': 0.6,
            'fuzzy': 0.2
        }
    
    def load_corpus(self) -> bool:
        """加载语料库"""
        try:
            # 加载传统检索
            traditional_count = self.traditional_retriever.load_documents()
            
            # 加载向量检索
            vector_count = 0
            if self.vector_retriever:
                # 先尝试加载预构建的索引
                if not self.vector_retriever.load_index():
                    # 如果没有预构建索引，则重新构建
                    vector_count = self.vector_retriever.load_documents()
                else:
                    vector_count = len(self.vector_retriever.documents)
            
            self.is_loaded = traditional_count > 0
            
            logger.info(f"RAG检索器加载完成 - 传统: {traditional_count}, 向量: {vector_count}")
            return self.is_loaded
            
        except Exception as e:
            logger.error(f"加载语料库失败: {e}")
            return False
    
    def search(self, query: str, top_k: int = 5, method: str = "hybrid") -> List[RetrievalResult]:
        """混合搜索"""
        if not self.is_loaded:
            logger.warning("语料库未加载")
            return []
        
        if method == "keyword":
            return self.traditional_retriever.search(query, top_k)
        elif method == "vector" and self.vector_retriever:
            return self.vector_retriever.search(query, top_k)
        elif method == "fuzzy":
            return self.traditional_retriever.fuzzy_search(query, top_k)
        elif method == "hybrid":
            return self._hybrid_search(query, top_k)
        else:
            # 默认使用传统检索
            return self.traditional_retriever.search(query, top_k)
    
    def _hybrid_search(self, query: str, top_k: int = 5) -> List[RetrievalResult]:
        """混合检索策略"""
        all_results = []
        
        # 关键词检索
        keyword_results = self.traditional_retriever.search(query, top_k * 2)
        for result in keyword_results:
            result.score *= self.retrieval_weights['keyword']
            all_results.append(result)
        
        # 向量检索
        if self.vector_retriever:
            vector_results = self.vector_retriever.search(query, top_k * 2)
            for result in vector_results:
                result.score *= self.retrieval_weights['vector']
                all_results.append(result)
        
        # 模糊检索（作为补充）
        if len(all_results) < top_k:
            fuzzy_results = self.traditional_retriever.fuzzy_search(query, top_k)
            for result in fuzzy_results:
                result.score *= self.retrieval_weights['fuzzy']
                all_results.append(result)
        
        # 去重并合并分数
        doc_scores = defaultdict(list)
        doc_results = {}
        
        for result in all_results:
            doc_scores[result.doc_id].append(result.score)
            if result.doc_id not in doc_results:
                doc_results[result.doc_id] = result
        
        # 合并分数（最大值策略）
        final_results = []
        for doc_id, scores in doc_scores.items():
            result = doc_results[doc_id]
            result.score = max(scores)
            result.retrieval_method = "hybrid"
            final_results.append(result)
        
        # 排序并返回top_k
        final_results.sort(key=lambda x: x.score, reverse=True)
        return final_results[:top_k]
    
    def search_by_type(self, query: str, doc_type: str, top_k: int = 3) -> List[RetrievalResult]:
        """按文档类型搜索"""
        results = self.search(query, top_k * 3)  # 获取更多结果再过滤
        
        # 过滤指定类型
        filtered_results = [r for r in results if r.doc_type == doc_type]
        
        return filtered_results[:top_k]
    
    def search_attractions(self, query: str, top_k: int = 3) -> List[RetrievalResult]:
        """搜索景点信息"""
        return self.search_by_type(query, 'attraction', top_k)
    
    def search_guides(self, query: str, top_k: int = 3) -> List[RetrievalResult]:
        """搜索游记攻略"""
        return self.search_by_type(query, 'guide', top_k)
    
    def search_reviews(self, query: str, top_k: int = 3) -> List[RetrievalResult]:
        """搜索用户评价"""
        return self.search_by_type(query, 'reviews', top_k)
    
    def get_stats(self) -> Dict:
        """获取检索器统计信息"""
        stats = {
            'is_loaded': self.is_loaded,
            'traditional_docs': len(self.traditional_retriever.documents),
            'vector_available': self.vector_retriever is not None,
            'vector_docs': len(self.vector_retriever.documents) if self.vector_retriever else 0,
            'total_keywords': len(self.traditional_retriever.keyword_index),
            'retrieval_weights': self.retrieval_weights
        }
        
        return stats

# 工具函数
def format_retrieval_results(results: List[RetrievalResult], max_content_length: int = 300) -> str:
    """格式化检索结果为文本"""
    if not results:
        return "没有找到相关信息。"
    
    formatted_parts = []
    
    for i, result in enumerate(results, 1):
        content = result.content
        if len(content) > max_content_length:
            content = content[:max_content_length] + "..."
        
        part = f"【相关信息 {i}】\n"
        part += f"标题：{result.title}\n"
        part += f"类型：{result.doc_type}\n"
        part += f"内容：{content}\n"
        part += f"相关度：{result.score:.2f}\n"
        
        formatted_parts.append(part)
    
    return "\n".join(formatted_parts)

def test_rag_retriever():
    """测试RAG检索器"""
    retriever = HybridRAGRetriever()
    
    # 加载语料库
    if not retriever.load_corpus():
        print("语料库加载失败")
        return
    
    # 测试查询
    test_queries = [
        "外滩有什么好玩的",
        "东方明珠门票多少钱",
        "上海博物馆开放时间",
        "迪士尼乐园攻略",
        "南京路购物推荐"
    ]
    
    for query in test_queries:
        print(f"\n查询：{query}")
        print("-" * 40)
        
        # 混合搜索
        results = retriever.search(query, top_k=3)
        formatted = format_retrieval_results(results)
        print(formatted)
        
        print("=" * 50)

if __name__ == "__main__":
    test_rag_retriever()

