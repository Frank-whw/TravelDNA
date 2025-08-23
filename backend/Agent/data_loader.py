#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据加载工具模块
提供统一的数据加载接口，支持多种格式和来源
"""

import os
import json
import logging
from typing import List, Tuple, Dict, Any
from config import Config

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataLoader:
    """统一数据加载器"""
    
    def __init__(self, base_dir: str = None):
        """
        初始化数据加载器
        
        Args:
            base_dir: 数据基础目录，默认使用配置文件中的路径
        """
        self.base_dir = base_dir or Config.KNOWLEDGE_BASE_PATH
        self.supported_extensions = {
            'text': ['.txt'],
            'json': ['.json'],
        }
        self.excluded_files = ['test_', 'crawl_stats.json']
        
    def _should_skip_file(self, filename: str) -> bool:
        """判断是否应该跳过某个文件"""
        return any(filename.startswith(prefix) for prefix in self.excluded_files)
    
    def _read_text_file(self, file_path: str) -> str:
        """读取文本文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read().strip()
        except Exception as e:
            logger.warning(f"读取文本文件失败 {file_path}: {e}")
            return ""
    
    def _read_json_file(self, file_path: str) -> str:
        """读取JSON文件并转换为文本"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return self._json_to_text(data)
        except Exception as e:
            logger.warning(f"读取JSON文件失败 {file_path}: {e}")
            return ""
    
    def _json_to_text(self, data: Any) -> str:
        """将JSON数据转换为文本格式"""
        if isinstance(data, dict):
            content_parts = []
            for key, value in data.items():
                if isinstance(value, (str, int, float)):
                    content_parts.append(f"{key}: {value}")
                elif isinstance(value, list):
                    # 处理列表数据
                    if value and isinstance(value[0], dict):
                        # 如果是字典列表，展开每个字典
                        for i, item in enumerate(value):
                            if isinstance(item, dict):
                                for sub_key, sub_value in item.items():
                                    content_parts.append(f"{key}_{i}_{sub_key}: {sub_value}")
                            else:
                                content_parts.append(f"{key}_{i}: {item}")
                    else:
                        # 简单列表直接连接
                        content_parts.append(f"{key}: {' '.join(str(item) for item in value)}")
                elif isinstance(value, dict):
                    # 嵌套字典
                    for sub_key, sub_value in value.items():
                        content_parts.append(f"{key}_{sub_key}: {sub_value}")
            return '\n'.join(content_parts)
        elif isinstance(data, list):
            return '\n'.join(str(item) for item in data)
        else:
            return str(data)
    
    def load_all_documents(self, show_progress: bool = True) -> Tuple[List[str], int]:
        """
        递归加载所有支持的文档
        
        Args:
            show_progress: 是否显示加载进度
            
        Returns:
            Tuple[List[str], int]: (文档列表, 文件数量)
        """
        if not os.path.exists(self.base_dir):
            logger.error(f"数据目录不存在: {self.base_dir}")
            return [], 0
        
        documents = []
        file_count = 0
        
        if show_progress:
            print(f"📂 开始加载数据目录: {os.path.abspath(self.base_dir)}")
        
        # 递归遍历目录
        for root, dirs, files in os.walk(self.base_dir):
            for file in files:
                # 跳过不需要的文件
                if self._should_skip_file(file):
                    continue
                
                file_path = os.path.join(root, file)
                content = ""
                
                # 根据文件扩展名处理
                if file.endswith(tuple(self.supported_extensions['text'])):
                    content = self._read_text_file(file_path)
                elif file.endswith(tuple(self.supported_extensions['json'])):
                    content = self._read_json_file(file_path)
                
                # 添加有效内容
                if content and content.strip():
                    documents.append(content)
                    file_count += 1
                    
                    if show_progress:
                        relative_path = os.path.relpath(file_path, self.base_dir)
                        print(f"✅ 加载文件: {relative_path}")
        
        if show_progress:
            print(f"\n🎉 成功加载 {file_count} 个文件，共 {len(documents)} 个文档")
        
        return documents, file_count
    
    def load_by_category(self) -> Dict[str, List[str]]:
        """
        按类别加载文档
        
        Returns:
            Dict[str, List[str]]: 按类别分组的文档
        """
        categories = {
            'attractions': [],
            'reviews': [], 
            'corpus': [],
            'numbered': [],
            'other': []
        }
        
        if not os.path.exists(self.base_dir):
            return categories
        
        for root, dirs, files in os.walk(self.base_dir):
            for file in files:
                if self._should_skip_file(file):
                    continue
                
                file_path = os.path.join(root, file)
                content = ""
                
                # 读取内容
                if file.endswith('.txt'):
                    content = self._read_text_file(file_path)
                elif file.endswith('.json'):
                    content = self._read_json_file(file_path)
                
                if not content:
                    continue
                
                # 分类
                relative_path = os.path.relpath(file_path, self.base_dir)
                if 'attractions' in relative_path:
                    categories['attractions'].append(content)
                elif 'reviews' in relative_path or 'review' in file.lower():
                    categories['reviews'].append(content)
                elif 'corpus' in relative_path:
                    categories['corpus'].append(content)
                elif file.replace('.txt', '').replace('.json', '').isdigit():
                    categories['numbered'].append(content)
                else:
                    categories['other'].append(content)
        
        return categories
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取数据统计信息"""
        if not os.path.exists(self.base_dir):
            return {"error": "数据目录不存在"}
        
        stats = {
            "total_files": 0,
            "total_documents": 0,
            "file_types": {},
            "categories": {},
            "total_size": 0
        }
        
        categories = self.load_by_category()
        documents, file_count = self.load_all_documents(show_progress=False)
        
        stats["total_files"] = file_count
        stats["total_documents"] = len(documents)
        stats["categories"] = {k: len(v) for k, v in categories.items()}
        
        # 统计文件类型
        for root, dirs, files in os.walk(self.base_dir):
            for file in files:
                if self._should_skip_file(file):
                    continue
                
                file_path = os.path.join(root, file)
                ext = os.path.splitext(file)[1].lower()
                
                if ext not in stats["file_types"]:
                    stats["file_types"][ext] = 0
                stats["file_types"][ext] += 1
                
                try:
                    stats["total_size"] += os.path.getsize(file_path)
                except:
                    pass
        
        # 转换文件大小为可读格式
        size_mb = stats["total_size"] / (1024 * 1024)
        stats["total_size_mb"] = round(size_mb, 2)
        
        return stats

# 全局数据加载器实例
default_loader = DataLoader()

# 便捷函数
def load_all_travel_data(data_dir: str = None, show_progress: bool = True) -> Tuple[List[str], int]:
    """
    加载所有旅游数据的便捷函数
    
    Args:
        data_dir: 数据目录，默认使用配置文件路径
        show_progress: 是否显示进度
        
    Returns:
        Tuple[List[str], int]: (文档列表, 文件数量)
    """
    loader = DataLoader(data_dir)
    return loader.load_all_documents(show_progress)

def get_data_statistics(data_dir: str = None) -> Dict[str, Any]:
    """获取数据统计信息的便捷函数"""
    loader = DataLoader(data_dir)
    return loader.get_statistics()

# 测试函数
if __name__ == "__main__":
    print("🧪 测试数据加载器...")
    
    # 测试加载所有数据
    docs, count = load_all_travel_data()
    print(f"✅ 加载完成: {count} 个文件, {len(docs)} 个文档")
    
    # 测试统计信息
    stats = get_data_statistics()
    print(f"\n📊 数据统计:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
