import os
import re
import requests
from dotenv import load_dotenv
import time


class TourismAssistant:
    def __init__(self, api_key=None, model="doubao-1-5-pro-32k-250115"):
        import requests
        import json
        self.api_url = "https://ark.cn-beijing.volces.com/api/v3/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {api_key or os.getenv('DOUBAO_API_KEY')}",
            "Content-Type": "application/json"
        }
        self.model = model
        load_dotenv()
        self.api_key = os.getenv('DOUBAO_API_KEY')
        self.documents = []

    def _call_doubao_api(self, prompt):
        payload = {
            "model": "doubao-1-5-pro-32k-250115",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7
        }
        try:
            response = requests.post(
                self.api_url,
                headers=self.headers,
                json=payload,
                timeout=30
            )
            if response.status_code == 200:
                return response.json()['choices'][0]['message']['content']
            return f"请求失败：{response.status_code} - {response.text}"
        except Exception as e:
            return f"发生异常：{str(e)}"

    def generate_response(self, query):
        # 简单关键词匹配
        keywords = re.findall(r'\w+', query.lower())
        context = '\n'.join(
            doc for doc in self.documents 
            if any(word in doc.lower() for word in keywords)
        )[:1000]
        
        prompt = f"""基于以下旅游信息：
{context}
请回答：{query}
回答时请使用中文并保持专业："""
        
        return self._call_doubao_api(prompt)