# RAG 模块

从 MaxKB 提取的独立 RAG（检索增强生成）功能模块。

## 功能特性

- ✅ 基于 PostgreSQL + pgvector 的向量存储
- ✅ 支持三种检索模式：向量检索、关键词检索、混合检索
- ✅ 文本自动分块
- ✅ 批量向量化
- ✅ 简化的 API 接口

## 安装

```bash
pip install -r requirements.txt
```

## 前置要求

1. **PostgreSQL** (>= 12) 并启用 pgvector 扩展
2. **Python** >= 3.8

## 快速开始

### 1. 初始化数据库

```sql
CREATE DATABASE rag_db;
\c rag_db
CREATE EXTENSION vector;
```

### 2. 使用示例

```python
from Rag import RAGClient, SearchMode
from langchain_openai import OpenAIEmbeddings

# 初始化客户端
db_url = "postgresql://user:password@localhost/rag_db"
embedding_model = OpenAIEmbeddings()

rag_client = RAGClient(db_url, embedding_model)

# 添加文档
rag_client.add_document(
    text="上海外滩是著名的旅游景点，开放时间24小时",
    knowledge_id="travel_kb_001",
    document_id="doc_001",
    paragraph_id="para_001"
)

# 检索
results = rag_client.search(
    query="上海外滩开放时间",
    knowledge_id_list=["travel_kb_001"],
    top_n=5,
    similarity=0.7,
    search_mode=SearchMode.EMBEDDING
)

for result in results:
    print(f"相似度: {result['similarity']:.2f}")
    print(f"段落ID: {result['paragraph_id']}")
```

## API 文档

### RAGClient

#### `add_document(text, knowledge_id, document_id, paragraph_id, **kwargs)`
添加单个文档到知识库。

#### `add_documents(documents)`
批量添加文档。

#### `search(query, knowledge_id_list, top_n=5, similarity=0.7, search_mode=SearchMode.EMBEDDING)`
检索知识库，返回相关段落。

#### `delete_knowledge(knowledge_id)`
删除整个知识库的向量数据。

#### `delete_document(document_id)`
删除文档的所有向量数据。

#### `delete_paragraph(paragraph_id)`
删除段落的向量数据。

## 检索模式

- **SearchMode.EMBEDDING**: 纯向量检索，基于语义相似度
- **SearchMode.KEYWORDS**: 关键词检索，基于全文搜索
- **SearchMode.BLEND**: 混合检索，结合向量和关键词

## 注意事项

1. 确保 PostgreSQL 已安装 pgvector 扩展
2. embedding 模型的维度需要与数据库中的向量维度匹配
3. 首次使用会自动创建 embedding 表


