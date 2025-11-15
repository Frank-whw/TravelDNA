"""
从文档加载到RAG知识库的脚本
使用方法：
    python load_rag_documents.py --files doc1.txt doc2.md --knowledge-id travel_kb_001
"""
import argparse
import sys
import os
from pathlib import Path

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from enhanced_travel_agent import EnhancedTravelAgent


def main():
    parser = argparse.ArgumentParser(description='从文档加载到RAG知识库')
    parser.add_argument('--files', nargs='+', required=True, help='文档文件路径列表')
    parser.add_argument('--knowledge-id', default='travel_kb_001', help='知识库ID')
    parser.add_argument('--storage-path', default='./rag_storage', help='RAG存储路径')
    
    args = parser.parse_args()
    
    # 设置存储路径环境变量
    os.environ['RAG_STORAGE_PATH'] = args.storage_path
    
    # 初始化Agent（会自动初始化RAG客户端）
    print("正在初始化Agent和RAG客户端...")
    try:
        agent = EnhancedTravelAgent()
    except Exception as e:
        print(f"❌ Agent初始化失败: {e}")
        return
    
    if not agent.rag_client:
        print("❌ RAG客户端未初始化，请检查配置")
        return
    
    print(f"✅ RAG客户端初始化成功")
    print(f"📁 存储路径: {args.storage_path}")
    print(f"📚 知识库ID: {args.knowledge_id}")
    print(f"📄 文件列表: {args.files}")
    print()
    
    # 加载文档
    print("正在加载文档...")
    agent.add_documents_from_files(args.files, args.knowledge_id)
    
    print()
    print("✅ 文档加载完成！")
    print(f"   现在可以在Agent中使用RAG检索功能了")


if __name__ == '__main__':
    main()

