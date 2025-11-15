"""
RAG客户端 - 基于BERT Embedding的检索增强生成
"""
from typing import List, Dict
from langchain_core.embeddings import Embeddings
from .vector_store import VectorStore, SearchMode
from .embedding import BERTEmbedding
import logging

logger = logging.getLogger(__name__)


class RAGClient:
    """基于BERT的RAG客户端"""
    
    def __init__(self, storage_path: str = "./rag_storage", embedding_model: Embeddings = None):
        """
        初始化RAG客户端
        
        Args:
            storage_path: 存储路径
            embedding_model: 向量化模型，如果为None则使用BERT
        """
        self.vector_store = VectorStore(storage_path)
        
        # 如果没有提供embedding模型，使用BERT
        if embedding_model is None:
            try:
                self.embedding_model = BERTEmbedding()
                logger.info("✅ 使用BERT Embedding模型")
            except Exception as e:
                logger.warning(f"⚠️ BERT模型初始化失败: {e}，将使用关键词检索模式")
                self.embedding_model = None
        else:
            self.embedding_model = embedding_model
    
    def add_document(self, text: str, knowledge_id: str, document_id: str,
                     paragraph_id: str, **kwargs):
        """
        添加文档到知识库
        
        Args:
            text: 文档文本
            knowledge_id: 知识库 ID
            document_id: 文档 ID
            paragraph_id: 段落 ID
        """
        if self.embedding_model is None:
            raise ValueError("需要提供 embedding_model 才能添加文档")
        
        self.vector_store.save(
            text=text,
            knowledge_id=knowledge_id,
            document_id=document_id,
            paragraph_id=paragraph_id,
            embedding=self.embedding_model,
            **kwargs
        )
    
    def add_documents(self, documents: List[Dict]):
        """
        批量添加文档
        
        Args:
            documents: 文档列表，每个文档包含: text, knowledge_id, document_id, paragraph_id
        """
        if self.embedding_model is None:
            raise ValueError("需要提供 embedding_model 才能添加文档")
        
        data_list = []
        for doc in documents:
            data_list.append({
                'text': doc['text'],
                'knowledge_id': doc['knowledge_id'],
                'document_id': doc['document_id'],
                'paragraph_id': doc['paragraph_id'],
                'source_id': doc.get('source_id', doc['paragraph_id']),
                'source_type': doc.get('source_type', '1'),
                'is_active': doc.get('is_active', True),
                'meta': doc.get('meta', {})
            })
        self.vector_store.batch_save(data_list, self.embedding_model)
    
    def search(self, query: str, knowledge_id_list: List[str],
               top_n: int = 5, similarity: float = 0.6,
               search_mode: SearchMode = SearchMode.BLEND) -> List[Dict]:
        """
        检索知识库
        
        Args:
            query: 查询文本
            knowledge_id_list: 知识库 ID 列表
            top_n: 返回 top N 个结果
            similarity: 相似度阈值
            search_mode: 检索模式（如果embedding_model为None，则只能使用KEYWORDS模式）
            
        Returns:
            检索结果列表
        """
        # 如果没有embedding模型，强制使用关键词检索
        if self.embedding_model is None:
            if search_mode != SearchMode.KEYWORDS:
                logger.warning("⚠️ 未提供embedding模型，自动切换到关键词检索模式")
            search_mode = SearchMode.KEYWORDS
        
        return self.vector_store.search(
            query_text=query,
            knowledge_id_list=knowledge_id_list,
            top_n=top_n,
            similarity=similarity,
            search_mode=search_mode,
            embedding=self.embedding_model
        )
    
    def delete_knowledge(self, knowledge_id: str):
        """删除知识库"""
        self.vector_store.delete_by_knowledge_id(knowledge_id)
    
    def delete_document(self, document_id: str):
        """删除文档"""
        self.vector_store.delete_by_document_id(document_id)
    
    def delete_paragraph(self, paragraph_id: str):
        """删除段落"""
        self.vector_store.delete_by_paragraph_id(paragraph_id)

