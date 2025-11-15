"""
向量存储模块 - 基于 PostgreSQL + pgvector
"""
import json
import os
from abc import ABC, abstractmethod
from enum import Enum
from typing import List, Dict, Optional
import psycopg
from psycopg.types import TypeInfo
from psycopg.types.vector import register_vector
from langchain_core.embeddings import Embeddings
import jieba


class SearchMode(Enum):
    """检索模式"""
    EMBEDDING = 'embedding'  # 向量检索
    KEYWORDS = 'keywords'    # 关键词检索
    BLEND = 'blend'         # 混合检索


class BaseVectorStore(ABC):
    """向量存储基类"""
    
    @abstractmethod
    def save(self, text: str, knowledge_id: str, document_id: str, 
             paragraph_id: str, embedding: Embeddings, **kwargs):
        """保存向量"""
        pass
    
    @abstractmethod
    def batch_save(self, data_list: List[Dict], embedding: Embeddings):
        """批量保存向量"""
        pass
    
    @abstractmethod
    def search(self, query_text: str, knowledge_id_list: List[str],
               top_n: int = 5, similarity: float = 0.7,
               search_mode: SearchMode = SearchMode.EMBEDDING,
               embedding: Embeddings = None) -> List[Dict]:
        """检索向量"""
        pass
    
    @abstractmethod
    def delete_by_knowledge_id(self, knowledge_id: str):
        """删除知识库的所有向量"""
        pass
    
    @abstractmethod
    def delete_by_document_id(self, document_id: str):
        """删除文档的所有向量"""
        pass


def text_to_chunk(text: str, chunk_size: int = 500, chunk_overlap: int = 50) -> List[str]:
    """文本分块"""
    if len(text) <= chunk_size:
        return [text]
    
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        start = end - chunk_overlap
        if start >= len(text):
            break
    return chunks


def to_ts_vector(text: str) -> str:
    """转换为 PostgreSQL ts_vector"""
    result = jieba.lcut(text, cut_all=True)
    return " ".join(result)


def to_query(text: str) -> str:
    """转换为查询字符串"""
    extract_tags = jieba.lcut(text, cut_all=True)
    return " ".join(extract_tags)


class VectorStore(BaseVectorStore):
    """PostgreSQL 向量存储实现"""
    
    def __init__(self, db_url: str):
        """
        初始化向量存储
        :param db_url: PostgreSQL 连接字符串，例如: postgresql://user:password@localhost/dbname
        """
        self.db_url = db_url
        self._ensure_vector_extension()
    
    def _get_connection(self):
        """获取数据库连接"""
        conn = psycopg.connect(self.db_url)
        # 注册 vector 类型
        info = TypeInfo.fetch(conn, 'vector')
        if info:
            register_vector(info, conn)
        return conn
    
    def _ensure_vector_extension(self):
        """确保 pgvector 扩展已启用"""
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
                conn.commit()
    
    def _ensure_table(self):
        """确保 embedding 表存在"""
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS embedding (
                        id VARCHAR(128) PRIMARY KEY,
                        knowledge_id VARCHAR(128),
                        document_id VARCHAR(128),
                        paragraph_id VARCHAR(128),
                        source_id VARCHAR(128),
                        source_type VARCHAR(5) DEFAULT '1',
                        is_active BOOLEAN DEFAULT TRUE,
                        embedding vector,
                        search_vector tsvector,
                        meta JSONB DEFAULT '{}',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                    CREATE INDEX IF NOT EXISTS embedding_knowledge_idx ON embedding(knowledge_id);
                    CREATE INDEX IF NOT EXISTS embedding_document_idx ON embedding(document_id);
                    CREATE INDEX IF NOT EXISTS embedding_paragraph_idx ON embedding(paragraph_id);
                    CREATE INDEX IF NOT EXISTS embedding_vector_idx ON embedding USING ivfflat (embedding vector_cosine_ops);
                """)
                conn.commit()
    
    def save(self, text: str, knowledge_id: str, document_id: str,
             paragraph_id: str, embedding: Embeddings, **kwargs):
        """保存单个向量"""
        self._ensure_table()
        
        # 向量化文本
        text_embedding = embedding.embed_query(text)
        embedding_str = json.dumps([float(x) for x in text_embedding])
        search_vector = to_ts_vector(text)
        
        # 生成 ID
        import uuid
        embedding_id = str(uuid.uuid4())
        
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO embedding (id, knowledge_id, document_id, paragraph_id,
                                         source_id, source_type, is_active, embedding, search_vector, meta)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s::vector, to_tsvector('simple', %s), %s)
                """, (
                    embedding_id, knowledge_id, document_id, paragraph_id,
                    kwargs.get('source_id', paragraph_id),
                    kwargs.get('source_type', '1'),
                    kwargs.get('is_active', True),
                    embedding_str,
                    search_vector,
                    json.dumps(kwargs.get('meta', {}))
                ))
                conn.commit()
    
    def batch_save(self, data_list: List[Dict], embedding: Embeddings):
        """批量保存向量"""
        if not data_list:
            return
        
        self._ensure_table()
        
        # 批量向量化
        texts = [item['text'] for item in data_list]
        embeddings = embedding.embed_documents(texts)
        
        import uuid
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                for idx, item in enumerate(data_list):
                    embedding_id = str(uuid.uuid4())
                    embedding_str = json.dumps([float(x) for x in embeddings[idx]])
                    search_vector = to_ts_vector(item['text'])
                    
                    cur.execute("""
                        INSERT INTO embedding (id, knowledge_id, document_id, paragraph_id,
                                             source_id, source_type, is_active, embedding, search_vector, meta)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s::vector, to_tsvector('simple', %s), %s)
                    """, (
                        embedding_id,
                        item.get('knowledge_id'),
                        item.get('document_id'),
                        item.get('paragraph_id'),
                        item.get('source_id', item.get('paragraph_id')),
                        item.get('source_type', '1'),
                        item.get('is_active', True),
                        embedding_str,
                        search_vector,
                        json.dumps(item.get('meta', {}))
                    ))
                conn.commit()
    
    def search(self, query_text: str, knowledge_id_list: List[str],
               top_n: int = 5, similarity: float = 0.7,
               search_mode: SearchMode = SearchMode.EMBEDDING,
               embedding: Embeddings = None) -> List[Dict]:
        """检索向量"""
        if not knowledge_id_list:
            return []
        
        if search_mode == SearchMode.EMBEDDING and embedding is None:
            raise ValueError("embedding 参数在 EMBEDDING 模式下是必需的")
        
        query_embedding = None
        if search_mode in [SearchMode.EMBEDDING, SearchMode.BLEND]:
            query_embedding = embedding.embed_query(query_text)
        
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                if search_mode == SearchMode.EMBEDDING:
                    return self._embedding_search(cur, query_embedding, knowledge_id_list, top_n, similarity)
                elif search_mode == SearchMode.KEYWORDS:
                    return self._keywords_search(cur, query_text, knowledge_id_list, top_n, similarity)
                elif search_mode == SearchMode.BLEND:
                    return self._blend_search(cur, query_text, query_embedding, knowledge_id_list, top_n, similarity)
    
    def _embedding_search(self, cur, query_embedding: List[float],
                          knowledge_id_list: List[str], top_n: int, similarity: float) -> List[Dict]:
        """向量检索"""
        embedding_str = json.dumps([float(x) for x in query_embedding])
        dim = len(query_embedding)
        
        # 使用参数化查询避免 SQL 注入，但向量维度需要动态
        cur.execute(f"""
            SELECT
                paragraph_id,
                (1 - (embedding <=> %s::vector)) as similarity,
                (1 - (embedding <=> %s::vector)) as comprehensive_score,
                knowledge_id, document_id, source_id, source_type
            FROM embedding
            WHERE knowledge_id = ANY(%s) AND is_active = TRUE
            ORDER BY embedding <=> %s::vector
            LIMIT %s
        """, (embedding_str, embedding_str, knowledge_id_list, embedding_str, top_n))
        
        results = []
        for row in cur.fetchall():
            if row[1] >= similarity:  # similarity threshold
                results.append({
                    'paragraph_id': row[0],
                    'similarity': float(row[1]),
                    'comprehensive_score': float(row[2]),
                    'knowledge_id': row[3],
                    'document_id': row[4],
                    'source_id': row[5],
                    'source_type': row[6]
                })
        return results
    
    def _keywords_search(self, cur, query_text: str,
                         knowledge_id_list: List[str], top_n: int, similarity: float) -> List[Dict]:
        """关键词检索"""
        query_str = to_query(query_text)
        
        cur.execute("""
            SELECT
                paragraph_id,
                ts_rank_cd(search_vector, websearch_to_tsquery('simple', %s), 32) as similarity,
                ts_rank_cd(search_vector, websearch_to_tsquery('simple', %s), 32) as comprehensive_score,
                knowledge_id, document_id, source_id, source_type
            FROM embedding
            WHERE knowledge_id = ANY(%s) AND is_active = TRUE
                AND search_vector @@ websearch_to_tsquery('simple', %s)
            ORDER BY similarity DESC
            LIMIT %s
        """, (query_str, query_str, knowledge_id_list, query_str, top_n))
        
        results = []
        for row in cur.fetchall():
            if row[1] >= similarity:
                results.append({
                    'paragraph_id': row[0],
                    'similarity': float(row[1]),
                    'comprehensive_score': float(row[2]),
                    'knowledge_id': row[3],
                    'document_id': row[4],
                    'source_id': row[5],
                    'source_type': row[6]
                })
        return results
    
    def _blend_search(self, cur, query_text: str, query_embedding: List[float],
                      knowledge_id_list: List[str], top_n: int, similarity: float) -> List[Dict]:
        """混合检索"""
        embedding_str = json.dumps([float(x) for x in query_embedding])
        query_str = to_query(query_text)
        
        cur.execute("""
            SELECT
                paragraph_id,
                (1 - (embedding <=> %s::vector) + 
                 ts_rank_cd(search_vector, websearch_to_tsquery('simple', %s), 32)) / 2 as similarity,
                (1 - (embedding <=> %s::vector) + 
                 ts_rank_cd(search_vector, websearch_to_tsquery('simple', %s), 32)) / 2 as comprehensive_score,
                knowledge_id, document_id, source_id, source_type
            FROM embedding
            WHERE knowledge_id = ANY(%s) AND is_active = TRUE
            ORDER BY similarity DESC
            LIMIT %s
        """, (embedding_str, query_str, embedding_str, query_str, knowledge_id_list, top_n))
        
        results = []
        for row in cur.fetchall():
            if row[1] >= similarity:
                results.append({
                    'paragraph_id': row[0],
                    'similarity': float(row[1]),
                    'comprehensive_score': float(row[2]),
                    'knowledge_id': row[3],
                    'document_id': row[4],
                    'source_id': row[5],
                    'source_type': row[6]
                })
        return results
    
    def delete_by_knowledge_id(self, knowledge_id: str):
        """删除知识库的所有向量"""
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM embedding WHERE knowledge_id = %s", (knowledge_id,))
                conn.commit()
    
    def delete_by_document_id(self, document_id: str):
        """删除文档的所有向量"""
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM embedding WHERE document_id = %s", (document_id,))
                conn.commit()
    
    def delete_by_paragraph_id(self, paragraph_id: str):
        """删除段落的向量"""
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM embedding WHERE paragraph_id = %s", (paragraph_id,))
                conn.commit()

