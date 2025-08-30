import os
import re

class QunarRAG:
    def __init__(self, data_path='data/'):
        self.data_path = data_path
        
    def load_documents(self):
        """
        加载文本文件并返回文档列表
        """
        documents = []
        for filename in os.listdir(self.data_path):
            if filename.endswith('.txt'):
                with open(os.path.join(self.data_path, filename), 'r', encoding='utf-8') as f:
                    documents.append(f.read())
        return documents
        
    def simple_search(self, query, documents, top_k=3):
        """
        基于关键词的简单搜索
        """
        keywords = re.findall(r'\w+', query.lower())
        results = []
        
        for doc in documents:
            score = sum(1 for word in keywords if word in doc.lower())
            if score > 0:
                results.append(doc)
        
        return results[:top_k]