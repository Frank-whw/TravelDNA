"""
RAG 模块使用示例
"""
from Rag import RAGClient, SearchMode
from langchain_openai import OpenAIEmbeddings
# 或者使用其他 embedding 模型
# from langchain_huggingface import HuggingFaceEmbeddings

# 配置
DB_URL = "postgresql://user:password@localhost/rag_db"
# 如果使用 OpenAI
# embedding_model = OpenAIEmbeddings(openai_api_key="your-api-key")
# 如果使用本地模型
# embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")

def example_add_documents():
    """示例：添加文档"""
    rag_client = RAGClient(DB_URL, embedding_model)
    
    # 添加单个文档
    rag_client.add_document(
        text="上海外滩是著名的旅游景点，位于黄浦江畔，开放时间24小时，免费参观。",
        knowledge_id="travel_kb_001",
        document_id="doc_001",
        paragraph_id="para_001"
    )
    
    # 批量添加文档
    documents = [
        {
            "text": "上海博物馆位于人民广场，开放时间9:00-17:00，周一闭馆。",
            "knowledge_id": "travel_kb_001",
            "document_id": "doc_001",
            "paragraph_id": "para_002"
        },
        {
            "text": "上海迪士尼乐园位于浦东新区，门票价格根据季节变化。",
            "knowledge_id": "travel_kb_001",
            "document_id": "doc_002",
            "paragraph_id": "para_003"
        }
    ]
    rag_client.add_documents(documents)
    print("文档添加完成")


def example_search():
    """示例：检索"""
    rag_client = RAGClient(DB_URL, embedding_model)
    
    # 向量检索
    results = rag_client.search(
        query="上海外滩的开放时间",
        knowledge_id_list=["travel_kb_001"],
        top_n=5,
        similarity=0.7,
        search_mode=SearchMode.EMBEDDING
    )
    
    print("检索结果：")
    for result in results:
        print(f"相似度: {result['similarity']:.2f}")
        print(f"段落ID: {result['paragraph_id']}")
        print(f"文档ID: {result['document_id']}")
        print("---")
    
    # 关键词检索
    results = rag_client.search(
        query="博物馆开放时间",
        knowledge_id_list=["travel_kb_001"],
        top_n=5,
        similarity=0.5,
        search_mode=SearchMode.KEYWORDS
    )
    
    # 混合检索
    results = rag_client.search(
        query="上海景点",
        knowledge_id_list=["travel_kb_001"],
        top_n=5,
        similarity=0.6,
        search_mode=SearchMode.BLEND
    )


def example_delete():
    """示例：删除数据"""
    rag_client = RAGClient(DB_URL, embedding_model)
    
    # 删除段落
    rag_client.delete_paragraph("para_001")
    
    # 删除文档
    rag_client.delete_document("doc_001")
    
    # 删除知识库
    rag_client.delete_knowledge("travel_kb_001")


if __name__ == "__main__":
    # 注意：需要先配置 embedding_model
    # embedding_model = OpenAIEmbeddings(openai_api_key="your-key")
    
    print("RAG 模块使用示例")
    print("请先配置 embedding_model 和 DB_URL")


