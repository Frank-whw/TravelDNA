"""
基于文件的RAG客户端 - 无需数据库
适用于只有文档的场景
"""
from typing import List, Dict
from langchain_core.embeddings import Embeddings
from .file_vector_store import FileVectorStore
from .vector_store import SearchMode


class FileRAGClient:
    """基于文件的RAG客户端"""
    
    def __init__(self, storage_path: str = "./rag_storage", embedding_model: Embeddings = None):
        """
        初始化文件RAG客户端
        :param storage_path: 存储路径
        :param embedding_model: 向量化模型（可选，如果为None则只支持关键词检索）
        """
        self.vector_store = FileVectorStore(storage_path)
        self.embedding_model = embedding_model
    
    def add_document(self, text: str, knowledge_id: str, document_id: str,
                     paragraph_id: str, **kwargs):
        """
        添加文档到知识库
        :param text: 文档文本
        :param knowledge_id: 知识库 ID
        :param document_id: 文档 ID
        :param paragraph_id: 段落 ID
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
        :param documents: 文档列表，每个文档包含: text, knowledge_id, document_id, paragraph_id
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
        :param query: 查询文本
        :param knowledge_id_list: 知识库 ID 列表
        :param top_n: 返回 top N 个结果
        :param similarity: 相似度阈值
        :param search_mode: 检索模式（如果embedding_model为None，则只能使用KEYWORDS模式）
        :return: 检索结果列表
        """
        # 如果没有embedding模型，强制使用关键词检索
        if self.embedding_model is None:
            if search_mode != SearchMode.KEYWORDS:
                print("⚠️ 未提供embedding模型，自动切换到关键词检索模式")
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

