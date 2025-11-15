import re
from model import TourismAssistant
from dotenv import load_dotenv
import os

# 读取所有旅游帖子数据
def load_travel_posts(data_dir):
    documents = []
    for i in range(1, 92):  # 从1到91号文件
        file_path = os.path.join(data_dir, f"{i}.txt")
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if content:  # 确保内容不为空
                    documents.append(content)
        except Exception as e:
            print(f"读取文件 {i}.txt 时出错: {e}")
    return documents

# 加载数据
data_dir = r"D:\Pycharm\PycharmProject\pythonProject\venv\RAG探索\data\data"
documents = load_travel_posts(data_dir)
print(f"成功加载 {len(documents)} 个旅游帖子")

# 文本分割
# 使用简单文本分割
chunk_size = 500
texts = []
for doc in documents:
    chunks = [doc[i:i+chunk_size] for i in range(0, len(doc), chunk_size)]
    texts.extend(chunks)
print(f"文本分割后共有 {len(texts)} 个文本块")

# 配置DeepSeek API
from dotenv import load_dotenv
load_dotenv()
DEEPSEEK_API_KEY = os.getenv("DOUBAO_API_KEY")
DEEPSEEK_API_BASE = "https://api.deepseek.com/v1"  # DeepSeek API基础地址

# 初始化豆包旅游助手
load_dotenv()
assistant = TourismAssistant(
    api_key=os.getenv("DOUBAO_API_KEY"),
    model="doubao-1-5-pro-32k-250115"
)
assistant.documents = documents

# 示例使用
response = assistant.generate_response("上海旅游推荐")
print(response)

# 简单文本分割
def simple_text_split(text, chunk_size=500):
    return [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]

# 关键词匹配搜索
def search_relevant_content(question, documents):
    keywords = re.findall(r'\w+', question.lower())
    results = []
    
    for doc in documents:
        score = sum(1 for word in keywords if word in doc.lower())
        if score > 0:
            results.append(doc[:200] + "...")
    return results[:3]

# 交互式问答循环
print("\n旅游问答系统已就绪！现在可以开始提问")

while True:
    question = input("\n请输入您的旅游问题（输入'exit'退出）：")
    if question.lower() == 'exit':
        break
    try:
        answer = assistant.generate_response(question)
        print("\n最终回答：", answer)
    except Exception as e:
        print(f"发生错误: {e}")
