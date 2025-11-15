#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强版智能旅行对话Agent
使用豆包Agent作为核心推理引擎，MCP服务提供实时数据支持
"""

import json
import logging
import os
import re
import requests
import urllib3
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import pandas as pd
from pathlib import Path
from threading import Lock
import jieba
import jieba.analyse

from config import (
    API_KEYS, AMAP_CONFIG, RAG_CONFIG, DEFAULT_CONFIG,
    get_api_key, get_config
)

# 导入新的模块化组件
# 使用try-except处理相对导入和绝对导入两种情况
try:
    # 相对导入（作为包的一部分）
    from .mcp import MCPServiceType, MCPClient, WeatherInfo, RouteInfo, POIInfo
    from .rag import RAGClient, SearchMode
    from .model.doubao_agent import DouBaoAgent
    try:
        from .model.deepseek_agent import DeepSeekAgent
        DEEPSEEK_AVAILABLE = True
    except ImportError:
        DeepSeekAgent = None
        DEEPSEEK_AVAILABLE = False
    from .model.models import TravelPreference, ThoughtProcess, UserContext, WeatherCondition, TrafficCondition, CrowdLevel
except ImportError:
    # 绝对导入（直接作为模块导入）
    from mcp import MCPServiceType, MCPClient, WeatherInfo, RouteInfo, POIInfo
    from rag import RAGClient, SearchMode
    from model.doubao_agent import DouBaoAgent
    try:
        from model.deepseek_agent import DeepSeekAgent
        DEEPSEEK_AVAILABLE = True
    except ImportError:
        DeepSeekAgent = None
        DEEPSEEK_AVAILABLE = False
    from model.models import TravelPreference, ThoughtProcess, UserContext, WeatherCondition, TrafficCondition, CrowdLevel

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 注意：所有枚举和数据结构已移至模块化组件
# - MCPServiceType, WeatherInfo, RouteInfo, POIInfo 从 .mcp 导入
# - TravelPreference, ThoughtProcess, UserContext, WeatherCondition, TrafficCondition, CrowdLevel 从 .model.models 导入
# - DouBaoAgent 从 .model.doubao_agent 导入
# - DeepSeekAgent 从 .model.deepseek_agent 导入（如果可用）

# 为了向后兼容，重新导出这些类供外部直接导入
__all__ = ['EnhancedTravelAgent', 'TravelPreference', 'UserContext', 'ThoughtProcess', 
           'WeatherCondition', 'TrafficCondition', 'CrowdLevel', 'MCPServiceType',
           'WeatherInfo', 'RouteInfo', 'POIInfo']

class EnhancedTravelAgent:
    """增强版智能旅行对话Agent"""
    
    def __init__(self):
        """初始化增强版Agent"""
        self.config = get_config()
        self.user_contexts = {}
        
        # 根据配置选择AI Provider（优先使用DeepSeek，如果没有则使用豆包）
        ai_provider = os.getenv('AI_PROVIDER', 'deepseek').lower()
        deepseek_api_key = get_api_key("DEEPSEEK")
        doubao_api_key = get_api_key("DOUBAO")
        
        # 初始化AI Agent
        if ai_provider == 'deepseek' and deepseek_api_key and DEEPSEEK_AVAILABLE and DeepSeekAgent:
            try:
                from config import Config
                self.ai_agent = DeepSeekAgent(
                    api_key=deepseek_api_key,
                    base_url=Config.DEEPSEEK_API_BASE,
                    model=Config.DEEPSEEK_MODEL
                )
                self.doubao_agent = self.ai_agent  # 保持向后兼容
                logger.info("✅ 使用DeepSeek Agent")
            except Exception as e:
                logger.warning(f"⚠️ DeepSeek Agent初始化失败: {e}，尝试使用豆包Agent")
                if doubao_api_key:
                    self.ai_agent = DouBaoAgent(doubao_api_key)
                    self.doubao_agent = self.ai_agent  # 保持向后兼容
                    logger.info("✅ 使用豆包Agent（DeepSeek初始化失败后的备选）")
                else:
                    raise ValueError("DeepSeek和豆包API密钥都未配置或初始化失败")
        elif doubao_api_key:
            self.ai_agent = DouBaoAgent(doubao_api_key)
            self.doubao_agent = self.ai_agent  # 保持向后兼容
            logger.info("✅ 使用豆包Agent")
        else:
            raise ValueError("缺少AI API密钥配置（需要DEEPSEEK_API_KEY或DOUBAO_API_KEY）")
        
        # API请求限流控制
        self._api_lock = Lock()
        self._last_api_call = {}  # 记录每个API的最后调用时间
        self._min_interval = 0.35  # 最小请求间隔（秒），确保不超过3次/秒
        
        # 加载Excel景点数据
        self.qunar_places = self._load_qunar_places()
        
        # 初始化MCP客户端
        self.mcp_client = MCPClient(
            api_lock=self._api_lock,
            last_api_call=self._last_api_call,
            min_interval=self._min_interval,
            qunar_places=self.qunar_places
        )
        
        # 初始化RAG客户端（使用BERT embedding）
        self.rag_client = None
        self._init_rag_client()
        
        # 上海地区关键词映射
        self.location_keywords = {
            # 浦东新区
            "浦东": ["东方明珠", "陆家嘴", "上海中心", "环球金融中心", "金茂大厦", "海洋馆", "科技馆", "迪士尼", "浦东机场"],
            "陆家嘴": ["东方明珠", "上海中心", "环球金融中心", "金茂大厦", "正大广场"],
            "迪士尼": ["上海迪士尼乐园", "迪士尼小镇", "奕欧来奥特莱斯"],
            
            # 黄浦区
            "外滩": ["外滩", "南京路", "和平饭店", "外白渡桥"],
            "人民广场": ["人民广场", "上海博物馆", "上海大剧院", "人民公园"],
            "豫园": ["豫园", "城隍庙", "南翔馒头店"],
            "南京路": ["南京路步行街", "第一百货", "新世界"],
            
            # 徐汇区
            "徐家汇": ["徐家汇", "太平洋百货", "港汇恒隆", "上海体育馆"],
            "淮海路": ["淮海路", "新天地", "田子坊", "思南路"],
            
            # 静安区
            "静安寺": ["静安寺", "久光百货", "嘉里中心"],
            "南京西路": ["静安嘉里中心", "梅龙镇广场", "中信泰富"],
            
            # 长宁区
            "虹桥": ["虹桥机场", "虹桥火车站", "龙之梦"],
            
            # 普陀区
            "长风公园": ["长风公园", "长风海洋世界"],
            
            # 虹口区
            "四川北路": ["多伦路", "鲁迅公园", "虹口足球场"],
            
            # 杨浦区
            "五角场": ["五角场", "合生汇", "大学路"],
            
            # 闵行区
            "七宝": ["七宝古镇", "七宝老街"],
            
            # 青浦区
            "朱家角": ["朱家角古镇", "课植园", "大清邮局"],
            
            # 松江区
            "佘山": ["佘山", "欢乐谷", "玛雅海滩"],
            
            # 嘉定区
            "南翔": ["古漪园", "南翔老街"]
        }
        
        # 活动类型关键词
        self.activity_keywords = {
            "购物": ["shopping", "买", "商场", "百货", "奥特莱斯", "专卖店"],
            "美食": ["吃", "餐厅", "小吃", "美食", "菜", "料理", "火锅", "烧烤"],
            "文化": ["博物馆", "展览", "历史", "文化", "古迹", "艺术"],
            "娱乐": ["游乐", "娱乐", "KTV", "电影", "酒吧", "夜生活"],
            "自然": ["公园", "花园", "湖", "江", "山", "海", "自然"],
            "商务": ["会议", "商务", "办公", "工作"],
            "亲子": ["孩子", "儿童", "亲子", "家庭", "带娃"]
        }
        
        # 天气相关关键词
        self.weather_keywords = ["天气", "下雨", "晴天", "阴天", "温度", "冷", "热", "风", "雪"]
        
        # 交通相关关键词
        self.traffic_keywords = ["开车", "自驾", "地铁", "公交", "打车", "走路", "骑车", "交通", "堵车"]
        
        # 时间相关关键词
        self.time_keywords = ["今天", "明天", "周末", "早上", "上午", "下午", "晚上", "夜里"]
        
        logger.info("🤖 增强版智能旅行对话Agent初始化完成")
    
    def _init_rag_client(self):
        """初始化RAG客户端（可选功能，支持数据库和文件两种模式）"""
        try:
            import os
            
            # 优先尝试使用数据库模式
            db_url = os.getenv('RAG_DB_URL', '')
            
            if db_url:
                # 数据库模式
                try:
                    from Rag import RAGClient, SearchMode
                    from langchain_openai import OpenAIEmbeddings
                    openai_api_key = os.getenv('OPENAI_API_KEY', '')
                    if openai_api_key:
                        embedding_model = OpenAIEmbeddings(openai_api_key=openai_api_key)
                        self.rag_client = RAGClient(db_url, embedding_model)
                        logger.info("✅ RAG客户端初始化成功（数据库模式）")
                        return
                except Exception as e:
                    logger.warning(f"⚠️ 数据库模式RAG初始化失败: {e}，尝试文件模式")
            
            # 文件模式（无需数据库）- 使用新的RAG模块（BERT embedding）
            try:
                from .rag import RAGClient
                
                # 设置存储路径
                storage_path = os.getenv('RAG_STORAGE_PATH', './rag_storage')
                
                # 使用BERT Embedding（默认）
                # RAGClient会自动初始化BERT模型，如果失败则使用关键词检索
                self.rag_client = RAGClient(storage_path=storage_path)
                logger.info(f"✅ RAG客户端初始化成功（BERT Embedding，存储路径: {storage_path}）")
                
                # 自动从data目录加载文档
                self._load_rag_documents_from_data()
                
            except ImportError:
                logger.warning("⚠️ 文件RAG模块导入失败，RAG功能将不可用")
                self.rag_client = None
            
        except Exception as e:
            logger.warning(f"⚠️ RAG客户端初始化失败: {e}")
            logger.info("   RAG功能将不可用，但不影响其他功能")
            self.rag_client = None
    
    def _load_rag_documents_from_data(self):
        """从data目录自动加载RAG文档"""
        if not self.rag_client:
            return
        
        try:
            from pathlib import Path
            import json
            import glob
            
            data_dir = Path(__file__).parent / "data"
            if not data_dir.exists():
                logger.warning(f"data目录不存在: {data_dir}")
                return
            
            knowledge_id = "travel_kb_001"
            documents = []
            doc_count = 0
            
            # 1. 加载rag_corpus/text_documents目录下的所有txt文件
            text_docs_dir = data_dir / "rag_corpus" / "text_documents"
            if text_docs_dir.exists():
                txt_files = list(text_docs_dir.glob("*.txt"))
                logger.info(f"📚 发现 {len(txt_files)} 个文本文档")
                
                for txt_file in txt_files:
                    try:
                        with open(txt_file, 'r', encoding='utf-8') as f:
                            text = f.read()
                        
                        if text.strip():
                            # 文本分块
                            from .rag.vector_store import text_to_chunk
                            chunks = text_to_chunk(text, chunk_size=500, chunk_overlap=50)
                            
                            for idx, chunk in enumerate(chunks):
                                documents.append({
                                    'text': chunk,
                                    'knowledge_id': knowledge_id,
                                    'document_id': f"txt_{doc_count}",
                                    'paragraph_id': f"para_{doc_count}_{idx}",
                                    'meta': {
                                        'file_name': txt_file.name,
                                        'source': 'rag_corpus',
                                        'chunk_index': idx
                                    }
                                })
                            
                            doc_count += 1
                            logger.debug(f"  ✅ 已加载: {txt_file.name} ({len(chunks)}个段落)")
                    except Exception as e:
                        logger.warning(f"  ⚠️ 加载文件失败 {txt_file.name}: {e}")
            
            # 2. 加载attractions目录下的JSON文件
            attractions_dir = data_dir / "attractions"
            if attractions_dir.exists():
                json_files = list(attractions_dir.glob("*.json"))
                logger.info(f"🏛️ 发现 {len(json_files)} 个景点JSON文件")
                
                for json_file in json_files:
                    try:
                        with open(json_file, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                        
                        # 提取景点信息文本
                        text_parts = []
                        if isinstance(data, dict):
                            # 提取所有有用的字段
                            if 'attraction_name' in data:
                                text_parts.append(f"景点名称：{data['attraction_name']}")
                            elif 'name' in data:
                                text_parts.append(f"景点名称：{data['name']}")
                            elif 'title' in data:
                                text_parts.append(f"景点名称：{data['title']}")
                            
                            if 'address' in data:
                                text_parts.append(f"地址：{data['address']}")
                            
                            if 'intro' in data:
                                text_parts.append(f"简介：{data['intro']}")
                            
                            if 'description' in data:
                                text_parts.append(f"详细描述：{data['description']}")
                            
                            # 提取交通指南
                            if 'transportation_guide' in data:
                                text_parts.append(f"交通指南：{data['transportation_guide']}")
                            elif 'transportation' in data:
                                text_parts.append(f"交通指南：{data['transportation']}")
                            
                            # 提取最佳季节
                            if 'best_season' in data:
                                text_parts.append(f"最佳季节：{data['best_season']}")
                            
                            # 提取开放时间
                            if 'opening_hours' in data:
                                text_parts.append(f"开放时间：{data['opening_hours']}")
                            
                            # 提取门票信息
                            if 'ticket_info' in data:
                                text_parts.append(f"门票信息：{data['ticket_info']}")
                            
                            # 提取评分
                            if 'rating' in data:
                                text_parts.append(f"评分：{data['rating']}")
                            
                            # 提取标签
                            if 'tags' in data:
                                tags = data['tags']
                                if isinstance(tags, list):
                                    # 过滤掉无效标签
                                    valid_tags = [t for t in tags if t and isinstance(t, str) and len(t.strip()) > 0 and t != '0']
                                    if valid_tags:
                                        text_parts.append(f"标签：{', '.join(valid_tags[:5])}")
                                elif isinstance(tags, str):
                                    text_parts.append(f"标签：{tags}")
                        
                        text = '\n'.join(text_parts)
                        if text.strip():
                            from .rag.vector_store import text_to_chunk
                            chunks = text_to_chunk(text, chunk_size=500, chunk_overlap=50)
                            
                            for idx, chunk in enumerate(chunks):
                                documents.append({
                                    'text': chunk,
                                    'knowledge_id': knowledge_id,
                                    'document_id': f"attraction_{doc_count}",
                                    'paragraph_id': f"para_{doc_count}_{idx}",
                                    'meta': {
                                        'file_name': json_file.name,
                                        'source': 'attractions',
                                        'chunk_index': idx
                                    }
                                })
                            
                            doc_count += 1
                            logger.debug(f"  ✅ 已加载: {json_file.name} ({len(chunks)}个段落)")
                    except Exception as e:
                        logger.warning(f"  ⚠️ 加载JSON文件失败 {json_file.name}: {e}")
            
            # 3. 加载reviews目录下的评论数据
            reviews_dir = data_dir / "reviews"
            if reviews_dir.exists():
                review_files = list(reviews_dir.glob("*.json"))
                logger.info(f"💬 发现 {len(review_files)} 个评论JSON文件")
                
                for review_file in review_files[:10]:  # 限制加载前10个，避免过多
                    try:
                        with open(review_file, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                        
                        # 提取评论文本
                        text_parts = []
                        if isinstance(data, list):
                            for review in data[:10]:  # 每个文件取前10条评论
                                if isinstance(review, dict):
                                    content = review.get('content', '')
                                    if content and len(content.strip()) > 10:  # 过滤太短的评论
                                        # 提取景点名称
                                        attraction = review.get('attraction_name', '')
                                        if attraction:
                                            text_parts.append(f"{attraction}的评论：{content[:200]}")  # 限制长度
                                        else:
                                            text_parts.append(f"评论：{content[:200]}")
                                    
                                    rating = review.get('rating')
                                    if rating and rating > 0:
                                        text_parts.append(f"评分：{rating}分")
                        elif isinstance(data, dict):
                            if 'reviews' in data:
                                for review in data['reviews'][:10]:
                                    content = review.get('content', '')
                                    if content and len(content.strip()) > 10:
                                        text_parts.append(f"评论：{content[:200]}")
                        
                        text = '\n'.join(text_parts)
                        if text.strip():
                            from .rag.vector_store import text_to_chunk
                            chunks = text_to_chunk(text, chunk_size=500, chunk_overlap=50)
                            
                            for idx, chunk in enumerate(chunks):
                                documents.append({
                                    'text': chunk,
                                    'knowledge_id': knowledge_id,
                                    'document_id': f"review_{doc_count}",
                                    'paragraph_id': f"para_{doc_count}_{idx}",
                                    'meta': {
                                        'file_name': review_file.name,
                                        'source': 'reviews',
                                        'chunk_index': idx
                                    }
                                })
                            
                            doc_count += 1
                            logger.debug(f"  ✅ 已加载: {review_file.name} ({len(chunks)}个段落)")
                    except Exception as e:
                        logger.warning(f"  ⚠️ 加载评论文件失败 {review_file.name}: {e}")
            
            # 批量添加到RAG知识库
            if documents:
                if hasattr(self.rag_client, 'add_documents'):
                    self.rag_client.add_documents(documents)
                    logger.info(f"✅ 成功从data目录加载 {len(documents)} 个文档段落到RAG知识库（来自 {doc_count} 个文件）")
                elif hasattr(self.rag_client, 'batch_save'):
                    # 如果RAG客户端支持batch_save
                    self.rag_client.batch_save(documents)
                    logger.info(f"✅ 成功从data目录加载 {len(documents)} 个文档段落到RAG知识库（来自 {doc_count} 个文件）")
                else:
                    logger.warning("RAG客户端不支持批量添加文档")
            else:
                logger.info("ℹ️ data目录下没有找到可加载的文档")
        
        except Exception as e:
            logger.error(f"从data目录加载RAG文档失败: {e}")
            import traceback
            logger.debug(traceback.format_exc())
    
    def add_documents_from_files(self, file_paths: List[str], knowledge_id: str = "travel_kb_001"):
        """
        从文件加载文档到RAG知识库
        
        :param file_paths: 文件路径列表（支持.txt, .md, .docx等）
        :param knowledge_id: 知识库ID
        """
        if not self.rag_client:
            logger.warning("RAG客户端未初始化，无法加载文档")
            return
        
        try:
            from pathlib import Path
            import docx
            
            documents = []
            doc_id = 0
            
            for file_path in file_paths:
                path = Path(file_path)
                if not path.exists():
                    logger.warning(f"文件不存在: {file_path}")
                    continue
                
                # 读取文件内容
                text = ""
                if path.suffix == '.txt' or path.suffix == '.md':
                    with open(path, 'r', encoding='utf-8') as f:
                        text = f.read()
                elif path.suffix == '.docx':
                    try:
                        doc = docx.Document(path)
                        text = '\n'.join([para.text for para in doc.paragraphs])
                    except Exception as e:
                        logger.warning(f"读取docx文件失败 {file_path}: {e}")
                        continue
                else:
                    logger.warning(f"不支持的文件格式: {path.suffix}")
                    continue
                
                # 文本分块
                from .rag.vector_store import text_to_chunk
                chunks = text_to_chunk(text, chunk_size=500, chunk_overlap=50)
                
                # 添加到文档列表
                for idx, chunk in enumerate(chunks):
                    documents.append({
                        'text': chunk,
                        'knowledge_id': knowledge_id,
                        'document_id': f"doc_{doc_id}",
                        'paragraph_id': f"para_{doc_id}_{idx}",
                        'meta': {
                            'file_path': str(file_path),
                            'file_name': path.name,
                            'chunk_index': idx
                        }
                    })
                
                doc_id += 1
                logger.info(f"✅ 已加载文件: {path.name} ({len(chunks)}个段落)")
            
            # 批量添加到RAG
            if documents:
                if hasattr(self.rag_client, 'add_documents'):
                    self.rag_client.add_documents(documents)
                    logger.info(f"✅ 成功添加 {len(documents)} 个文档段落到RAG知识库")
                else:
                    logger.warning("RAG客户端不支持批量添加文档")
        
        except Exception as e:
            logger.error(f"从文件加载文档失败: {e}")
    
    def _load_qunar_places(self) -> pd.DataFrame:
        """加载去哪儿景点数据"""
        try:
            excel_path = Path(__file__).parent / "data" / "qunar_place.xlsx"
            if excel_path.exists():
                df = pd.read_excel(excel_path)
                logger.info(f"✅ 成功加载去哪儿景点数据: {len(df)}条记录")
                return df
            else:
                logger.warning(f"⚠️ 去哪儿景点数据文件不存在: {excel_path}")
                return pd.DataFrame()
        except Exception as e:
            logger.error(f"❌ 加载去哪儿景点数据失败: {e}")
            return pd.DataFrame()
    
    def _search_qunar_places(self, keyword: str, limit: int = 10) -> List[POIInfo]:
        """从Excel数据中搜索景点"""
        if self.qunar_places.empty:
            return []
        
        try:
            # 在name和intro列中搜索关键词
            mask = (
                self.qunar_places['name'].str.contains(keyword, case=False, na=False) |
                self.qunar_places['intro'].str.contains(keyword, case=False, na=False)
            )
            results = self.qunar_places[mask].head(limit)
            
            pois = []
            for _, row in results.iterrows():
                # 解析districts获取区域信息
                districts = str(row.get('districts', ''))
                address = districts.replace('·', '') if districts else ''
                
                # 解析point获取坐标
                point = str(row.get('point', ''))
                
                poi = POIInfo(
                    name=str(row.get('name', '')),
                    address=address,
                    rating=float(row.get('score', 0) or 0),
                    business_hours="",
                    price=f"{row.get('price', 0)}元" if row.get('price', 0) else "免费",
                    distance="",
                    category=str(row.get('star', '')),
                    reviews=[]
                )
                pois.append(poi)
            
            logger.info(f"从Excel数据中搜索到{len(pois)}个景点: {keyword}")
            return pois
        except Exception as e:
            logger.error(f"搜索Excel数据失败: {e}")
            return []
    
    def process_user_request(self, user_input: str, user_id: str = "default", show_thoughts: bool = True, return_thoughts: bool = False) -> Any:
        """
        处理用户请求的主入口 - 基于思考链的智能Agent系统
        
        流程：
        1. 深度理解用户需求，生成思考链（Thoughts）
        2. 从思考链中提取关键词和所需API
        3. 根据关键词智能调用相应的API
        4. 收集并整理实时数据
        5. 基于数据生成最终决策
        
        Args:
            user_input: 用户输入
            user_id: 用户ID
            show_thoughts: 是否展示思考过程给用户（控制台输出）
            return_thoughts: 是否在返回结果中包含思考过程（供API使用）
            
        Returns:
            如果return_thoughts=True，返回字典 {"response": str, "thoughts": list}
            否则返回字符串（回复内容）
        """
        logger.info(f"👤 用户 {user_id} 输入: {user_input}")
        
        # 获取或创建用户上下文
        if user_id not in self.user_contexts:
            self.user_contexts[user_id] = UserContext(
                user_id=user_id,
                conversation_history=[],
                travel_preferences=TravelPreference()
            )
        
        context = self.user_contexts[user_id]
        
        # 记录用户输入
        context.conversation_history.append({
            "role": "user",
            "content": user_input,
            "timestamp": datetime.now().isoformat()
        })
        
        print("\n" + "="*80)
        print("🧠 知小旅 - 智能旅游规划助手")
        print("="*80)
        
        # ============ Step 0: 解析标签（如果存在） ============
        tags = self._parse_tags_from_input(user_input)
        if any(tags.values()):
            print(f"\n🏷️  检测到标签：基础标签{len(tags['基础标签'])}个，偏好标签{len(tags['偏好标签'])}个，特殊标签{len(tags['特殊标签'])}个")
        
        # ============ Step 1: 深度理解需求并生成思考链 ============
        print("\n📋 Step 1: 深度理解您的需求...")
        thoughts = self._generate_thought_chain(user_input, context)
        
        if show_thoughts:
            self._display_thoughts(thoughts)
        
        # ============ Step 2: 从思考链中提取关键信息并进行分词 ============
        print("\n🔍 Step 2: 提取关键信息、分词并规划策略...")
        extracted_info = self._extract_info_from_thoughts(thoughts, user_input)
        # 保存分词结果到extracted_info中
        if thoughts:
            extracted_info['tokenized_data'] = self._tokenize_thoughts(thoughts)
        # 保存标签信息
        extracted_info['tags'] = tags
        # 生成用户画像
        user_profile = self._generate_user_profile(extracted_info, tags)
        extracted_info['user_profile'] = user_profile
        self._display_extracted_info(extracted_info)
        
        # 如果return_thoughts=True，在step2后返回思考结果（仅第一次调用时）
        # 通过检查context中是否已有思考结果来判断是否是第一次调用
        if return_thoughts and not hasattr(context, '_thinking_sent'):
            simplified_thoughts = []
            for t in thoughts[:2]:  # 只返回前2步的思考过程
                simplified_thoughts.append({
                    "step": t.step,
                    "thought": t.thought,
                    "keywords": t.keywords[:15],  # 返回更多关键词用于展示
                    "reasoning": t.reasoning,
                    "icon": self._get_thought_icon(t.step)
                })
            
            # 标记已发送思考结果
            context._thinking_sent = True
            
            # 返回step1、2的思考结果
            return {
                "response": "正在分析你的需求，请稍候...",  # 提示信息
                "thoughts": simplified_thoughts,
                "extracted_info": {
                    "travel_days": extracted_info.get('travel_days', 1),
                    "locations": extracted_info.get('locations', []),
                    "enhanced_locations": extracted_info.get('enhanced_locations', []),  # 包含完整的景点信息
                    "keywords": extracted_info.get('keywords', []),
                    "activity_types": extracted_info.get('activity_types', []),
                    "budget_info": extracted_info.get('budget_info', {}),
                    "companions": self._format_companions(extracted_info.get('companions', {})) if extracted_info.get('companions') else None,
                    "emotional_context": self._format_emotional_context(extracted_info.get('emotional_context', {})) if extracted_info.get('emotional_context') else None,
                    "preferences": extracted_info.get('preferences', {}),
                    "user_intent_summary": extracted_info.get('user_intent_summary', ''),
                    "tags": extracted_info.get('tags', {})  # 包含标签信息
                },
                "status": "thinking"  # 标识这是思考阶段
            }
        
        # ============ Step 3: 智能API调用决策 ============
        print("\n🤖 Step 3: 决定需要调用的API服务...")
        api_plan = self._plan_api_calls(extracted_info, thoughts)
        self._display_api_plan(api_plan)
        
        # ============ Step 4: 执行API调用并收集数据（包括MCP和RAG） ============
        print("\n📡 Step 4: 调用MCP和RAG服务收集实时数据和知识...")
        real_time_data = self._execute_api_calls(api_plan, extracted_info, context, thoughts)
        
        # ============ Step 5: 综合分析并生成最终决策 ============
        print("\n💡 Step 5: 综合分析，生成最优旅游攻略...")
        final_response = self._generate_final_decision(
            user_input, thoughts, extracted_info, real_time_data, context
        )
        
        # 记录Agent回复
        context.conversation_history.append({
            "role": "assistant",
            "content": final_response,
            "thoughts": [{"step": t.step, "thought": t.thought, "keywords": t.keywords} for t in thoughts],
            "timestamp": datetime.now().isoformat()
        })
        
        # 记忆沉淀：记录用户偏好（如果出现3次以上）
        self._update_user_memory(context, extracted_info, tags)
        
        print("\n" + "="*80)
        print("✅ 规划完成！")
        print("="*80 + "\n")
        
        # 根据参数决定返回格式
        if return_thoughts:
            # 返回完整信息，包含思考过程（供API使用）
            simplified_thoughts = []
            for t in thoughts:
                simplified_thoughts.append({
                    "step": t.step,
                    "thought": t.thought,
                    "keywords": t.keywords[:5],  # 只返回前5个关键词
                    "reasoning": t.reasoning,
                    "icon": self._get_thought_icon(t.step)
                })
            
            return {
                "response": final_response,
                "thoughts": [],  # 最终回复时不返回思考过程
                "extracted_info": {
                    "travel_days": extracted_info.get('travel_days', 1),
                    "locations": extracted_info.get('locations', []),
                    "enhanced_locations": extracted_info.get('enhanced_locations', []),  # 包含完整的景点信息
                    "keywords": extracted_info.get('keywords', []),
                    "activity_types": extracted_info.get('activity_types', []),
                    "budget_info": extracted_info.get('budget_info', {}),
                    "companions": self._format_companions(extracted_info.get('companions', {})) if extracted_info.get('companions') else None,
                    "emotional_context": self._format_emotional_context(extracted_info.get('emotional_context', {})) if extracted_info.get('emotional_context') else None,
                    "preferences": extracted_info.get('preferences', {}),
                    "user_intent_summary": extracted_info.get('user_intent_summary', ''),
                    "tags": extracted_info.get('tags', {}),  # 包含标签信息
                    "user_profile": extracted_info.get('user_profile', {})  # 包含用户画像
                },
                "status": "completed"  # 标识已完成
            }
        else:
            # 仅返回回复文本
            return final_response
    
    def _get_thought_icon(self, step: int) -> str:
        """根据步骤获取合适的图标"""
        icons = ["🤔", "💡", "🌤️", "🗺️", "🚦", "📊", "✨"]
        return icons[min(step - 1, len(icons) - 1)]
    
    # ==================== 思考链系统核心方法 ====================
    
    def _generate_thought_chain(self, user_input: str, context: UserContext) -> List[ThoughtProcess]:
        """生成思考链 - 通过Agent引导生成详细的思考过程"""
        system_prompt = """你是一个专业的上海旅游规划专家。请深入分析用户的需求，并生成一个详细的、结构化的思考过程。

你的任务是：
1. **深度理解用户需求**：分析用户的核心意图、情感需求、同伴关系、时间安排、预算等
2. **识别关键信息**：提取地点、时间、活动类型、特殊偏好等关键要素
3. **规划信息收集策略**：明确需要哪些实时数据（天气、POI、交通、人流等）来支持决策
4. **思考推理过程**：详细说明每一步的推理逻辑和原因

请以JSON格式返回你的思考过程，要求：
- 思考步骤要详细、具体，体现你的推理过程
- 关键词要全面，包括地点、时间、活动、情感等各个方面
- 明确说明需要哪些API服务来获取数据
- 每个步骤都要有清晰的推理原因

格式示例：
{
  "thoughts": [
    {
      "step": 1,
      "thought": "首先，我需要理解用户的核心需求。用户想要规划3天的上海旅游，这是一个多日行程规划需求。",
      "keywords": ["3天", "上海", "旅游", "行程规划"],
      "api_needs": ["天气", "景点", "POI"],
      "reasoning": "多日行程需要查询未来3天的天气情况，以便合理安排室内外活动；同时需要搜索适合3天游览的景点和POI信息"
    },
    {
      "step": 2,
      "thought": "用户提到了具体地点：外滩、豫园。这些是上海的热门景点，需要查询这些地点的详细信息、开放时间、周边推荐等。",
      "keywords": ["外滩", "豫园", "景点", "开放时间"],
      "api_needs": ["POI", "导航"],
      "reasoning": "需要调用POI搜索API获取这些景点的详细信息，并可能需要规划这些景点之间的路线"
    }
  ]
}

请确保思考过程详细、全面，能够为后续的信息收集和方案生成提供充分的基础。"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"请详细分析这个旅游需求，并给出完整的思考过程：\n\n{user_input}"}
        ]
        
        try:
            response = self.doubao_agent.generate_response(messages)
            
            # 尝试解析JSON响应
            思考数据 = self._parse_thought_response(response)
            
            # 转换为ThoughtProcess对象
            thoughts = []
            for idx, thought_data in enumerate(思考数据.get("thoughts", []), 1):
                thought = ThoughtProcess(
                    step=idx,
                    thought=thought_data.get("thought", ""),
                    keywords=thought_data.get("keywords", []),
                    mcp_services=self._map_api_needs_to_services(thought_data.get("api_needs", [])),
                    reasoning=thought_data.get("reasoning", ""),
                    timestamp=datetime.now().isoformat()
                )
                thoughts.append(thought)
            
            # 如果AI没有返回有效的思考链，使用备用方法
            if not thoughts:
                logger.warning("Agent未返回有效思考链，使用备用方法")
                thoughts = self._fallback_thought_generation(user_input, context)
            
            return thoughts
            
        except Exception as e:
            logger.error(f"思考链生成失败: {e}")
            # 使用备用方法
            return self._fallback_thought_generation(user_input, context)
    
    def _parse_thought_response(self, response: str) -> Dict:
        """解析AI的思考响应"""
        try:
            # 尝试提取JSON部分
            import re
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                return json.loads(json_match.group())
            else:
                # 如果没有JSON，返回空字典
                return {"thoughts": []}
        except:
            return {"thoughts": []}
    
    def _map_api_needs_to_services(self, api_needs: List[str]) -> List[MCPServiceType]:
        """将API需求映射到服务类型"""
        service_map = {
            "天气": MCPServiceType.WEATHER,
            "weather": MCPServiceType.WEATHER,
            "景点": MCPServiceType.POI,
            "poi": MCPServiceType.POI,
            "餐厅": MCPServiceType.POI,
            "美食": MCPServiceType.POI,
            "导航": MCPServiceType.NAVIGATION,
            "路线": MCPServiceType.NAVIGATION,
            "navigation": MCPServiceType.NAVIGATION,
            "交通": MCPServiceType.TRAFFIC,
            "路况": MCPServiceType.TRAFFIC,
            "traffic": MCPServiceType.TRAFFIC,
            "人流": MCPServiceType.CROWD,
            "crowd": MCPServiceType.CROWD
        }
        
        services = []
        for need in api_needs:
            service = service_map.get(need.lower())
            if service and service not in services:
                services.append(service)
        
        return services
    
    def _fallback_thought_generation(self, user_input: str, context: UserContext) -> List[ThoughtProcess]:
        """备用思考链生成方法 - 基于规则"""
        thoughts = []
        keywords = self._extract_keywords(user_input)
        detected_locations, activity_types = self._analyze_user_intent(user_input)
        travel_days = self._extract_travel_days(user_input)
        
        # Thought 1: 理解需求
        thoughts.append(ThoughtProcess(
            step=1,
            thought=f"用户需要规划{travel_days}天的上海旅游攻略",
            keywords=keywords + [f"{travel_days}天"] + detected_locations,
            mcp_services=[],
            reasoning="首先理解用户的基本需求和时间安排",
            timestamp=datetime.now().isoformat()
        ))
        
        # Thought 2: 地点分析
        if detected_locations:
            thoughts.append(ThoughtProcess(
                step=2,
                thought=f"用户提到了具体地点：{', '.join(detected_locations)}",
                keywords=detected_locations,
                mcp_services=[MCPServiceType.POI],
                reasoning="需要搜索这些地点的详细信息和周边景点",
                timestamp=datetime.now().isoformat()
            ))
        else:
            thoughts.append(ThoughtProcess(
                step=2,
                thought="用户没有指定具体地点，需要推荐上海经典景点",
                keywords=["上海", "经典景点"],
                mcp_services=[MCPServiceType.POI],
                reasoning="推荐适合游览时长的经典景点组合",
                timestamp=datetime.now().isoformat()
            ))
        
        # Thought 3: 天气考虑
        thoughts.append(ThoughtProcess(
            step=3,
            thought=f"需要查询未来{travel_days}天的天气情况",
            keywords=["天气", "预报"],
            mcp_services=[MCPServiceType.WEATHER],
            reasoning="根据天气情况调整室内外活动安排",
            timestamp=datetime.now().isoformat()
        ))
        
        # Thought 4: 交通规划
        if len(detected_locations) > 1 or "交通" in user_input or "路线" in user_input:
            thoughts.append(ThoughtProcess(
                step=4,
                thought="需要规划景点间的交通路线",
                keywords=["导航", "路线", "交通"],
                mcp_services=[MCPServiceType.NAVIGATION, MCPServiceType.TRAFFIC],
                reasoning="提供最优交通方案，考虑路况避免拥堵",
                timestamp=datetime.now().isoformat()
            ))
        
        return thoughts
    
    def _display_thoughts(self, thoughts: List[ThoughtProcess]):
        """展示思考过程"""
        print("\n💭 AI思考过程：")
        print("-" * 80)
        for thought in thoughts:
            print(f"\n  步骤 {thought.step}: {thought.thought}")
            if thought.keywords:
                print(f"  关键词: {', '.join(thought.keywords)}")
            if thought.mcp_services:
                services = [s.value for s in thought.mcp_services]
                print(f"  需要API: {', '.join(services)}")
            print(f"  原因: {thought.reasoning}")
    
    def _tokenize_thoughts(self, thoughts: List[ThoughtProcess]) -> Dict[str, Any]:
        """对Agent给出的思考过程进行分词，提取关键信息用于MCP和RAG调用"""
        # 合并所有思考过程的文本
        all_thought_text = []
        all_keywords = []
        
        for thought in thoughts:
            # 合并思考内容、关键词和推理过程
            thought_text = f"{thought.thought} {thought.reasoning}"
            all_thought_text.append(thought_text)
            all_keywords.extend(thought.keywords)
        
        combined_text = " ".join(all_thought_text)
        
        # 使用jieba进行分词和关键词提取
        # 提取关键词（使用TF-IDF算法）
        keywords_tfidf = jieba.analyse.extract_tags(combined_text, topK=20, withWeight=False)
        
        # 提取关键词（使用TextRank算法）
        keywords_textrank = jieba.analyse.textrank(combined_text, topK=20, withWeight=False)
        
        # 合并关键词，去重
        all_extracted_keywords = list(set(keywords_tfidf + keywords_textrank + all_keywords))
        
        # 分词结果
        words = list(jieba.cut(combined_text))
        
        # 提取地点、时间、活动等特定类型的关键词
        location_keywords = []
        time_keywords = []
        activity_keywords = []
        
        # 地点相关关键词
        location_patterns = ["上海", "外滩", "豫园", "东方明珠", "南京路", "人民广场", "田子坊", 
                            "新天地", "城隍庙", "朱家角", "迪士尼", "陆家嘴", "徐家汇", "静安寺"]
        # 时间相关关键词
        time_patterns = ["天", "日", "小时", "早上", "上午", "下午", "晚上", "周末", "工作日"]
        # 活动相关关键词
        activity_patterns = ["旅游", "游览", "参观", "美食", "购物", "拍照", "体验", "探索"]
        
        for keyword in all_extracted_keywords:
            if any(pattern in keyword for pattern in location_patterns):
                location_keywords.append(keyword)
            elif any(pattern in keyword for pattern in time_patterns):
                time_keywords.append(keyword)
            elif any(pattern in keyword for pattern in activity_patterns):
                activity_keywords.append(keyword)
        
        return {
            "words": words,
            "keywords": all_extracted_keywords,
            "location_keywords": location_keywords,
            "time_keywords": time_keywords,
            "activity_keywords": activity_keywords,
            "thought_text": combined_text
        }
    
    def _extract_info_from_thoughts(self, thoughts: List[ThoughtProcess], user_input: str) -> Dict[str, Any]:
        """从思考链中提取关键信息 - 包括人文因素和分词结果"""
        # 对思考过程进行分词
        tokenized_data = self._tokenize_thoughts(thoughts)
        
        # 收集所有关键词（包括Agent给出的和分词提取的）
        all_keywords = []
        for thought in thoughts:
            all_keywords.extend(thought.keywords)
        all_keywords.extend(tokenized_data["keywords"])
        all_keywords = list(set(all_keywords))  # 去重
        
        # 提取地点（优先使用分词结果中的地点关键词）
        locations = self._extract_locations_from_input(user_input)
        if tokenized_data["location_keywords"]:
            locations.extend(tokenized_data["location_keywords"])
            locations = list(set(locations))  # 去重
        
        # 智能选择关键词进行输入提示API调用
        enhanced_locations = []
        
        # 按优先级排序关键词
        priority_keywords = self._prioritize_keywords_for_inputtips(all_keywords, user_input)
        
        # 只对前5个最重要的关键词使用输入提示API（分批调用避免QPS超限）
        # 过滤掉纯数字和无效关键词
        valid_keywords = [kw for kw in priority_keywords[:5] if not kw.isdigit() and len(kw.strip()) > 1]
        
        for i, keyword in enumerate(valid_keywords):
            try:
                # 每次调用间隔0.4秒，确保不超过QPS限制
                if i > 0:
                    time.sleep(0.4)
                
                # 使用输入提示API验证和增强地点信息
                tips = self.get_inputtips(keyword, city="上海", citylimit=True)
                if tips:
                    # 只保留有效的地点建议（过滤掉不相关的结果）
                    valid_tips = [tip for tip in tips if self._is_valid_location(tip.get('name', ''), keyword)]
                    if valid_tips:
                        # 确保包含完整的景点信息（名称、地址、区域等）
                        full_suggestions = []
                        for tip in valid_tips[:5]:
                            full_suggestions.append({
                                "name": tip.get('name', ''),  # 完整景点名称
                                "address": tip.get('address', ''),  # 完整地址
                                "district": tip.get('district', ''),  # 区域
                                "location": tip.get('location', ''),  # 坐标
                                "typecode": tip.get('typecode', ''),  # 类型代码
                                "id": tip.get('id', '')  # ID
                            })
                        
                        enhanced_locations.append({
                            "keyword": keyword,
                            "suggestions": full_suggestions,  # 完整的景点信息
                            "priority": i + 1
                        })
                        logger.info(f"输入提示API成功: {keyword} -> {len(valid_tips)}个有效建议")
            except Exception as e:
                logger.warning(f"输入提示API调用失败 for {keyword}: {e}")
                # 继续处理下一个关键词，不中断整个流程
        
        # 提取活动类型
        activity_types = []
        for activity, kws in self.activity_keywords.items():
            if any(kw in user_input for kw in kws):
                activity_types.append(activity)
        
        # 提取时间信息
        travel_days = self._extract_travel_days(user_input)
        
        # ========== 新增：提取人文因素 ==========
        
        # 提取社交关系和同伴信息
        companions = self._extract_companions(user_input)
        
        # 提取情感需求和氛围
        emotional_context = self._extract_emotional_context(user_input)
        
        # 提取预算信息
        budget_info = self._extract_budget(user_input)
        
        # 提取特殊偏好
        preferences = self._extract_preferences(user_input)
        
        # 提取完整的用户原始意图（保留所有细节）
        user_intent_summary = self._summarize_user_intent(user_input, thoughts)
        
        return {
            "keywords": list(set(all_keywords)),
            "locations": locations,
            "enhanced_locations": enhanced_locations,
            "activity_types": activity_types,
            "travel_days": travel_days,
            "route_info": self._extract_route_from_input(user_input),
            # 人文因素
            "companions": companions,
            "emotional_context": emotional_context,
            "budget_info": budget_info,
            "preferences": preferences,
            "user_intent_summary": user_intent_summary,
            "original_input": user_input  # 保留原始输入
        }
    
    def _extract_companions(self, user_input: str) -> Dict[str, Any]:
        """提取同伴信息"""
        companions = {
            "type": None,
            "count": 1,
            "details": []
        }
        
        # 检测同伴类型
        companion_patterns = {
            "女朋友": {"type": "romantic_partner", "gender": "female", "relationship": "girlfriend"},
            "男朋友": {"type": "romantic_partner", "gender": "male", "relationship": "boyfriend"},
            "老婆": {"type": "spouse", "gender": "female", "relationship": "wife"},
            "老公": {"type": "spouse", "gender": "male", "relationship": "husband"},
            "爱人": {"type": "spouse", "relationship": "spouse"},
            "女朋友": {"type": "romantic_partner", "relationship": "girlfriend"},
            "父母": {"type": "family", "relationship": "parents", "count": 2},
            "爸妈": {"type": "family", "relationship": "parents", "count": 2},
            "孩子": {"type": "family", "relationship": "children"},
            "小孩": {"type": "family", "relationship": "children"},
            "宝宝": {"type": "family", "relationship": "baby"},
            "家人": {"type": "family", "relationship": "family"},
            "朋友": {"type": "friends", "relationship": "friends"},
            "闺蜜": {"type": "friends", "relationship": "best_friend", "gender": "female"},
            "兄弟": {"type": "friends", "relationship": "brother"},
            "同事": {"type": "colleagues", "relationship": "colleagues"},
            "团队": {"type": "team", "relationship": "team"}
        }
        
        for pattern, info in companion_patterns.items():
            if pattern in user_input:
                companions["type"] = info["type"]
                companions["details"].append(info)
                if "count" in info:
                    companions["count"] += info["count"]
                else:
                    companions["count"] += 1
                break
        
        return companions
    
    def _extract_emotional_context(self, user_input: str) -> Dict[str, Any]:
        """提取情感需求和氛围"""
        emotional_context = {
            "mood": [],
            "atmosphere": [],
            "avoid": [],
            "desire": []
        }
        
        # 情绪和氛围关键词
        mood_keywords = {
            "浪漫": "romantic",
            "温馨": "cozy",
            "轻松": "relaxed",
            "安静": "quiet",
            "热闹": "lively",
            "文艺": "artistic",
            "小资": "petty_bourgeois",
            "高端": "upscale",
            "奢华": "luxury",
            "朴实": "simple",
            "地道": "authentic",
            "特色": "unique"
        }
        
        for keyword, mood in mood_keywords.items():
            if keyword in user_input:
                emotional_context["mood"].append(mood)
                emotional_context["atmosphere"].append(keyword)
        
        # 避开的内容
        avoid_keywords = ["避开", "不要", "别去", "不想", "讨厌"]
        for avoid_kw in avoid_keywords:
            if avoid_kw in user_input:
                # 提取避开的具体内容
                if "人多" in user_input or "拥挤" in user_input or "热门" in user_input:
                    emotional_context["avoid"].append("crowded_places")
                if "商业" in user_input:
                    emotional_context["avoid"].append("commercial")
                if "网红" in user_input:
                    emotional_context["avoid"].append("internet_famous")
        
        # 期望体验
        desire_keywords = {
            "感受": "experience",
            "体验": "experience",
            "了解": "understand",
            "风土人情": "local_culture",
            "当地生活": "local_life",
            "历史": "history",
            "文化": "culture",
            "美食": "cuisine"
        }
        
        for keyword, desire in desire_keywords.items():
            if keyword in user_input:
                emotional_context["desire"].append(desire)
        
        return emotional_context
    
    def _extract_budget(self, user_input: str) -> Dict[str, Any]:
        """提取预算信息"""
        import re
        
        budget_info = {
            "amount": None,
            "level": "medium",
            "constraint": None
        }
        
        # 提取具体金额
        amount_patterns = [
            r'(\d+)万',  # 如：2万
            r'(\d+)千',  # 如：5千
            r'(\d+)元',  # 如：20000元
            r'预算.*?(\d+)',  # 预算xxx
            r'不低于.*?(\d+)',  # 不低于xxx
            r'不超过.*?(\d+)',  # 不超过xxx
        ]
        
        for pattern in amount_patterns:
            match = re.search(pattern, user_input)
            if match:
                amount = int(match.group(1))
                if '万' in pattern:
                    amount *= 10000
                elif '千' in pattern:
                    amount *= 1000
                budget_info["amount"] = amount
                break
        
        # 判断预算等级
        if budget_info["amount"]:
            if budget_info["amount"] >= 20000:
                budget_info["level"] = "high"
            elif budget_info["amount"] >= 10000:
                budget_info["level"] = "medium_high"
            elif budget_info["amount"] >= 5000:
                budget_info["level"] = "medium"
            else:
                budget_info["level"] = "low"
        
        # 预算约束
        if "不低于" in user_input:
            budget_info["constraint"] = "minimum"
        elif "不超过" in user_input or "最多" in user_input:
            budget_info["constraint"] = "maximum"
        
        # 关键词判断
        if "经济" in user_input or "省钱" in user_input or "便宜" in user_input:
            budget_info["level"] = "low"
        elif "奢华" in user_input or "高端" in user_input or "不差钱" in user_input:
            budget_info["level"] = "high"
        
        return budget_info
    
    def _extract_preferences(self, user_input: str) -> List[str]:
        """提取特殊偏好"""
        preferences = []
        
        preference_keywords = {
            "风土人情": "local_culture",
            "当地特色": "local_specialty",
            "非热门": "off_the_beaten_path",
            "小众": "niche",
            "网红": "internet_famous",
            "打卡": "photo_spots",
            "美食": "food_focused",
            "购物": "shopping_focused",
            "历史": "history_focused",
            "自然": "nature_focused",
            "艺术": "art_focused",
            "夜生活": "nightlife",
            "慢节奏": "slow_paced",
            "深度游": "in_depth"
        }
        
        for keyword, preference in preference_keywords.items():
            if keyword in user_input:
                preferences.append(preference)
        
        return preferences
    
    def _summarize_user_intent(self, user_input: str, thoughts: List[ThoughtProcess]) -> str:
        """总结用户完整意图，保留所有人文细节"""
        # 使用AI来总结，保留人文细节
        try:
            summary_prompt = f"""请用一句话总结用户的旅游需求，要保留所有人文细节和情感因素。

用户输入：{user_input}

要求：
1. 保留同伴信息（如：女朋友、父母、孩子等）
2. 保留情感需求（如：浪漫、温馨、避开人群等）
3. 保留预算信息
4. 保留特殊偏好
5. 用温暖、人性化的语言表达

示例：
输入："我想带女朋友去上海玩3天"
输出："您计划和女朋友一起在上海度过浪漫的3天"

请总结："""
            
            messages = [{"role": "user", "content": summary_prompt}]
            summary = self.doubao_agent.generate_response(messages)
            return summary.strip()
        except:
            # 如果AI失败，返回原始输入
            return user_input
    
    def _display_extracted_info(self, info: Dict[str, Any]):
        """展示提取的信息 - 包括人文因素"""
        print("\n📌 提取的关键信息：")
        print("-" * 80)
        
        # 显示用户意图总结（最重要，放在最前面）
        if info.get('user_intent_summary'):
            print(f"  💭 需求理解: {info['user_intent_summary']}")
            print()
        
        # 显示同伴信息
        if info.get('companions') and info['companions']['type']:
            companion_desc = self._format_companions(info['companions'])
            print(f"  👥 同伴信息: {companion_desc}")
        
        # 显示情感需求和氛围
        if info.get('emotional_context'):
            emotional_desc = self._format_emotional_context(info['emotional_context'])
            if emotional_desc:
                print(f"  💝 情感需求: {emotional_desc}")
        
        # 显示预算信息
        if info.get('budget_info') and info['budget_info']['amount']:
            budget_desc = self._format_budget(info['budget_info'])
            print(f"  💰 预算信息: {budget_desc}")
        
        # 显示特殊偏好
        if info.get('preferences'):
            pref_desc = self._format_preferences(info['preferences'])
            print(f"  ⭐ 特殊偏好: {pref_desc}")
        
        # 基础信息
        print(f"\n  📅 旅行天数: {info['travel_days']}天")
        
        if info['locations']:
            print(f"  📍 提到的地点: {', '.join(info['locations'])}")
        
        if info['enhanced_locations']:
            print(f"  🔍 智能识别的地点:")
            for loc in info['enhanced_locations'][:5]:
                if loc.get('suggestions'):
                    for suggestion in loc['suggestions'][:2]:
                        name = suggestion.get('name', '未知')
                        address = suggestion.get('address', suggestion.get('district', ''))
                        display_text = f"{name}"
                        if address:
                            display_text += f"（{address}）"
                        print(f"     • {display_text}")
                else:
                    print(f"     • {loc['keyword']}: 未找到")
        
        if info['activity_types']:
            print(f"  🎯 活动类型: {', '.join(info['activity_types'])}")
        
        if info['route_info']:
            print(f"  🗺️  路线: {info['route_info']['start']} → {info['route_info']['end']}")
    
    def _format_companions(self, companions: Dict[str, Any]) -> str:
        """格式化同伴信息"""
        if not companions['details']:
            return "独自一人"
        
        companion_names = {
            "girlfriend": "女朋友",
            "boyfriend": "男朋友",
            "wife": "妻子",
            "husband": "丈夫",
            "spouse": "爱人",
            "parents": "父母",
            "children": "孩子",
            "baby": "宝宝",
            "family": "家人",
            "friends": "朋友",
            "best_friend": "闺蜜",
            "brother": "兄弟",
            "colleagues": "同事",
            "team": "团队"
        }
        
        parts = []
        for detail in companions['details']:
            relationship = detail.get('relationship', '')
            name = companion_names.get(relationship, relationship)
            parts.append(name)
        
        if companions['count'] > 2:
            return f"{', '.join(parts)} ({companions['count']}人)"
        else:
            return ', '.join(parts)
    
    def _format_emotional_context(self, emotional_context: Dict[str, Any]) -> str:
        """格式化情感需求"""
        parts = []
        
        if emotional_context['atmosphere']:
            parts.append(f"氛围偏好：{', '.join(emotional_context['atmosphere'])}")
        
        if emotional_context['avoid']:
            avoid_names = {
                "crowded_places": "避开人群",
                "commercial": "避开商业区",
                "internet_famous": "避开网红景点"
            }
            avoid_desc = [avoid_names.get(a, a) for a in emotional_context['avoid']]
            parts.append(f"{', '.join(avoid_desc)}")
        
        if emotional_context['desire']:
            desire_names = {
                "experience": "想要体验",
                "local_culture": "感受风土人情",
                "local_life": "了解当地生活",
                "history": "了解历史",
                "culture": "了解文化",
                "cuisine": "品尝美食"
            }
            desire_desc = [desire_names.get(d, d) for d in emotional_context['desire'][:2]]
            parts.append(f"{', '.join(desire_desc)}")
        
        return '；'.join(parts) if parts else ""
    
    def _format_budget(self, budget_info: Dict[str, Any]) -> str:
        """格式化预算信息"""
        if budget_info['amount']:
            amount_str = f"{budget_info['amount']}元"
            if budget_info['constraint'] == 'minimum':
                return f"不低于{amount_str} ({budget_info['level']}档次)"
            elif budget_info['constraint'] == 'maximum':
                return f"不超过{amount_str} ({budget_info['level']}档次)"
            else:
                return f"约{amount_str} ({budget_info['level']}档次)"
        else:
            level_names = {
                "low": "经济型",
                "medium": "中等",
                "medium_high": "中高端",
                "high": "高端"
            }
            return level_names.get(budget_info['level'], budget_info['level'])
    
    def _format_preferences(self, preferences: List[str]) -> str:
        """格式化特殊偏好"""
        preference_names = {
            "local_culture": "风土人情",
            "local_specialty": "当地特色",
            "off_the_beaten_path": "小众景点",
            "niche": "小众体验",
            "internet_famous": "网红打卡",
            "photo_spots": "拍照打卡",
            "food_focused": "美食之旅",
            "shopping_focused": "购物为主",
            "history_focused": "历史文化",
            "nature_focused": "自然风光",
            "art_focused": "艺术体验",
            "nightlife": "夜生活",
            "slow_paced": "慢节奏",
            "in_depth": "深度游"
        }
        
        pref_desc = [preference_names.get(p, p) for p in preferences[:5]]
        return ', '.join(pref_desc)
    
    def _plan_api_calls(self, extracted_info: Dict[str, Any], thoughts: List[ThoughtProcess]) -> Dict[str, Any]:
        """规划API调用策略"""
        api_plan = {
            "weather": True,
            "poi": True,
            "navigation": False,
            "traffic": False,
            "crowd": False,
            "inputtips": False
        }
        
        # 从thoughts中收集需要的API
        for thought in thoughts:
            for service in thought.mcp_services:
                if service == MCPServiceType.WEATHER:
                    api_plan["weather"] = True
                elif service == MCPServiceType.POI:
                    api_plan["poi"] = True
                elif service == MCPServiceType.NAVIGATION:
                    api_plan["navigation"] = True
                elif service == MCPServiceType.TRAFFIC:
                    api_plan["traffic"] = True
                elif service == MCPServiceType.CROWD:
                    api_plan["crowd"] = True
        
        # 如果有多天行程，必须查天气
        if extracted_info['travel_days'] > 1:
            api_plan["weather"] = True
        
        # 如果有地点或路线，需要POI和导航
        if extracted_info['locations'] or extracted_info['route_info']:
            api_plan["poi"] = True
            api_plan["navigation"] = True
            api_plan["traffic"] = True
        
        # 如果有模糊的关键词，使用输入提示API
        if extracted_info['keywords'] and not extracted_info['locations']:
            api_plan["inputtips"] = True
        
        return api_plan
    
    def _display_api_plan(self, api_plan: Dict[str, Any]):
        """展示API调用计划"""
        print("\n📞 API调用计划：")
        print("-" * 80)
        
        api_icons = {
            "weather": "🌤️  天气API",
            "poi": "🏛️  POI搜索API",
            "navigation": "🗺️  导航API",
            "traffic": "🚦 路况API",
            "crowd": "👥 人流API",
            "inputtips": "💡 输入提示API"
        }
        
        for api, enabled in api_plan.items():
            if enabled:
                print(f"  ✓ {api_icons.get(api, api)}")
    
    def _call_rag_service(self, query: str, knowledge_id_list: List[str] = None) -> List[Dict]:
        """调用RAG服务检索知识库"""
        try:
            # 检查是否有RAG客户端可用
            if not hasattr(self, 'rag_client') or self.rag_client is None:
                logger.warning("RAG客户端未初始化，跳过RAG检索")
                return []
            
            # 如果没有指定知识库ID，使用默认的
            if knowledge_id_list is None:
                knowledge_id_list = ["travel_kb_001"]  # 默认旅游知识库ID
            
            # 调用RAG搜索 - 使用新的RAG模块
            search_mode = SearchMode.BLEND
            
            results = self.rag_client.search(
                query=query,
                knowledge_id_list=knowledge_id_list,
                top_n=5,
                similarity=0.6,
                search_mode=search_mode  # 混合检索模式
            )
            
            logger.info(f"RAG检索成功，返回{len(results)}条结果")
            return results
            
        except Exception as e:
            logger.error(f"RAG服务调用失败: {e}")
            return []
    
    def _execute_api_calls(self, api_plan: Dict[str, Any], extracted_info: Dict[str, Any], context: UserContext, thoughts: List[ThoughtProcess] = None) -> Dict[str, Any]:
        """执行API调用 - 包括MCP和RAG功能"""
        real_time_data = {}
        
        # 从思考链中获取分词结果（如果已计算）
        tokenized_data = extracted_info.get('tokenized_data', {})
        if not tokenized_data and thoughts:
            tokenized_data = self._tokenize_thoughts(thoughts)
            extracted_info['tokenized_data'] = tokenized_data
        
        locations = extracted_info['locations'] if extracted_info['locations'] else ["上海"]
        
        # ========== 调用RAG服务 ==========
        print("  📚 正在调用RAG知识库检索...")
        rag_results = []
        
        # 构建RAG查询：使用思考过程的文本和关键词
        if tokenized_data:
            # 使用思考文本作为查询
            rag_query = tokenized_data.get('thought_text', '')
            if not rag_query:
                # 如果没有思考文本，使用关键词组合
                keywords = tokenized_data.get('keywords', [])
                rag_query = ' '.join(keywords[:10])  # 使用前10个关键词
            
            if rag_query:
                rag_results = self._call_rag_service(rag_query)
                if rag_results:
                    real_time_data["rag"] = {
                        "query": rag_query,
                        "results": rag_results,
                        "count": len(rag_results)
                    }
                    logger.info(f"RAG检索成功，获得{len(rag_results)}条相关知识")
        
        # ========== 调用MCP服务 ==========
        
        # 调用天气API
        if api_plan["weather"]:
            print("  🌤️  正在获取天气信息...")
            weather_data = {}
            for location in locations:
                try:
                    weather = self.get_weather(location, context.travel_preferences.start_date)
                except Exception as e:
                    logger.warning(f"获取{location}天气失败: {e}")
                    weather = []
                weather_data[location] = weather or []
            
            if not weather_data:
                weather_data["上海"] = []
            real_time_data["weather"] = weather_data
        
        # 调用输入提示API（智能选择关键词）
        if api_plan["inputtips"] and extracted_info['keywords']:
            print("  💡 正在使用输入提示API识别地点...")
            tips_data = {}
            
            # 使用智能优先级排序
            priority_keywords = self._prioritize_keywords_for_inputtips(extracted_info['keywords'], extracted_info.get('original_input', ''))
            
            # 对前3个高优先级关键词调用API
            for i, keyword in enumerate(priority_keywords[:3]):
                try:
                    # 控制调用频率
                    if i > 0:
                        time.sleep(0.4)
                    
                    tips = self.get_inputtips(keyword, city="上海", citylimit=True)
                    if tips:
                        tips_data[keyword] = {
                            "suggestions": tips[:5],
                            "priority": i + 1,
                            "count": len(tips)
                        }
                        logger.info(f"输入提示API成功: {keyword} -> {len(tips)}个建议")
                except Exception as e:
                    logger.warning(f"输入提示API调用失败 for {keyword}: {e}")
            
            real_time_data["inputtips"] = tips_data
        
        # 调用POI API
        if api_plan["poi"]:
            print("  🏛️  正在搜索景点和餐厅...")
            poi_data = {}
            for location in locations:
                attractions = self.search_poi("景点", location, "110000")
                poi_data[f"{location}_景点"] = attractions[:5]
                
                restaurants = self.search_poi("餐厅", location, "050000")
                poi_data[f"{location}_餐饮"] = restaurants[:5]
            real_time_data["poi"] = poi_data
        
        # 调用导航API
        if api_plan["navigation"]:
            print("  🗺️  正在规划路线...")
            navigation_data = {}
            
            if extracted_info['route_info']:
                routes = self.get_navigation_routes(
                    extracted_info['route_info']['start'],
                    extracted_info['route_info']['end']
                )
                navigation_data[f"{extracted_info['route_info']['start']}_to_{extracted_info['route_info']['end']}"] = routes
            elif len(locations) >= 2:
                for i in range(len(locations) - 1):
                    routes = self.get_navigation_routes(locations[i], locations[i+1])
                    navigation_data[f"{locations[i]}_to_{locations[i+1]}"] = routes
            
            real_time_data["navigation"] = navigation_data
        
        # 调用路况API
        if api_plan["traffic"]:
            print("  🚦 正在检查路况...")
            traffic_data = {}
            for location in locations:
                traffic = self.get_traffic_status(location)
                traffic_data[location] = traffic
            real_time_data["traffic"] = traffic_data
        
        print("  ✅ 数据收集完成！")
        return real_time_data
    
    def _build_environmental_recommendations(self, extracted_info: Dict[str, Any],
                                             real_time_data: Dict[str, Any],
                                             context: UserContext) -> Dict[str, Any]:
        """融合天气与POI的综合推荐分析"""
        locations = list(extracted_info.get('locations') or [])
        weather_map = real_time_data.get("weather") or {}
        poi_map = real_time_data.get("poi") or {}
        
        if not locations:
            derived_locations = list(weather_map.keys())
            if not derived_locations:
                derived_locations = [key.split("_")[0] for key in poi_map.keys()]
            locations = derived_locations or ["上海"]
        
        preferences = set()
        for key in ("activity_types", "preferences"):
            pref_list = extracted_info.get(key) or []
            preferences.update(pref_list)
        
        budget_info = extracted_info.get('budget_info') or {}
        budget_level = budget_info.get('level')
        
        recommendations = []
        
        for location in locations:
            weather_records = self._get_weather_records_for_location(weather_map, location)
            weather_analysis = self._analyze_weather_condition(weather_records)
            
            collected_pois = self._collect_pois_for_location(poi_map, location)
            scored_pois = []
            for category_label, poi in collected_pois:
                score, reasons = self._score_poi_candidate(
                    poi,
                    category_label,
                    weather_analysis,
                    preferences,
                    budget_level
                )
                scored_pois.append({
                    "name": poi.name,
                    "category": category_label or poi.category,
                    "address": poi.address,
                    "score": round(score, 1),
                    "reasons": reasons,
                    "price": poi.price,
                    "business_hours": poi.business_hours
                })
            
            scored_pois.sort(key=lambda x: x["score"], reverse=True)
            
            recommendations.append({
                "location": location,
                "weather": weather_analysis,
                "top_pois": scored_pois[:5],
                "indoor_priority": not weather_analysis.get("suitable_for_outdoor", True),
                "data_available": bool(collected_pois)
            })
        
        overall_tips = self._generate_overall_tips(recommendations)
        
        return {
            "generated_at": datetime.now().isoformat(),
            "locations": recommendations,
            "overall_tips": overall_tips
        }
    
    def _get_weather_records_for_location(self, weather_map: Dict[str, Any], location: str) -> List[WeatherInfo]:
        """获取指定地点的天气记录，必要时回退到其他地点"""
        if not weather_map:
            return []
        
        if location in weather_map and weather_map[location]:
            return weather_map[location]
        
        for key, records in weather_map.items():
            if location in key and records:
                return records
        
        for records in weather_map.values():
            if records:
                return records
        
        return []
    
    def _analyze_weather_condition(self, weather_records: List[WeatherInfo]) -> Dict[str, Any]:
        """根据天气数据生成可用性评估"""
        if not weather_records:
            return {
                "summary": "暂无天气数据",
                "condition": "unknown",
                "temperature": "未知",
                "average_temperature": None,
                "suitable_for_outdoor": False,
                "advice": "暂无可靠天气信息，请提醒用户出行前再次确认天气预报。",
                "score": 50
            }
        
        record = weather_records[0] if isinstance(weather_records, list) else weather_records
        weather_text = getattr(record, "weather", "") or ""
        temperature_text = getattr(record, "temperature", "") or ""
        temp_value = self._parse_temperature_value(temperature_text)
        
        condition = "moderate"
        score = 70
        suitable_for_outdoor = True
        advice = "天气整体适宜，可以灵活安排室内外活动。"
        
        if any(keyword in weather_text for keyword in ["雷", "暴雨", "台风", "大风", "冰雹"]):
            condition = "extreme"
            score = 20
            suitable_for_outdoor = False
            advice = "天气较为极端，请优先选择室内活动，并留意官方安全预警。"
        elif "雨" in weather_text:
            condition = "rainy"
            score = 45
            suitable_for_outdoor = False
            advice = "有降雨，建议准备雨具，把重点放在室内或半室内项目上。"
        elif "雪" in weather_text:
            condition = "snow"
            score = 40
            suitable_for_outdoor = False
            advice = "可能有降雪或湿冷，注意防滑保暖，多安排室内体验。"
        elif any(keyword in weather_text for keyword in ["阴", "多云"]):
            condition = "cloudy"
            score = 65
            advice = "多云天气，光线柔和，适合轻松散步或艺术展览等活动。"
        elif any(keyword in weather_text for keyword in ["晴", "阳"]):
            condition = "sunny"
            score = 85
            advice = "晴朗天气，适合户外活动，也别忘了补水和防晒。"
        
        if temp_value is not None:
            if temp_value >= 33:
                score -= 10
                advice += " 气温偏高，户外时段请安排在早晚并注意补水。"
            elif temp_value <= 5:
                score -= 10
                suitable_for_outdoor = False
                advice += " 气温较低，需要防寒保暖，可多考虑室内选项。"
        
        return {
            "summary": weather_text or "暂无天气描述",
            "condition": condition,
            "temperature": temperature_text or "未知",
            "average_temperature": temp_value,
            "suitable_for_outdoor": suitable_for_outdoor,
            "advice": advice,
            "score": max(min(score, 100), 0)
        }
    
    def _parse_temperature_value(self, temperature_text: str) -> Optional[float]:
        """解析温度字符串，返回平均温度"""
        if not temperature_text:
            return None
        matches = re.findall(r'-?\d+', temperature_text)
        if not matches:
            return None
        values = [int(m) for m in matches]
        if not values:
            return None
        return sum(values) / len(values)
    
    def _collect_pois_for_location(self, poi_map: Dict[str, List[POIInfo]], location: str) -> List[Tuple[str, POIInfo]]:
        """收集与地点相关的POI"""
        if not poi_map:
            return []
        
        collected: List[Tuple[str, POIInfo]] = []
        for key, pois in poi_map.items():
            if not pois:
                continue
            key_location, _, category_label = key.partition("_")
            matches_location = (key_location == location) or (location in key_location) or (location in key)
            if matches_location:
                for poi in pois:
                    normalized_poi = poi
                    if isinstance(poi, dict):
                        normalized_poi = POIInfo(
                            name=poi.get("name", ""),
                            address=poi.get("address", ""),
                            rating=float(poi.get("rating", 0) or 0),
                            business_hours=poi.get("business_hours", "") or poi.get("open_time", ""),
                            price=str(poi.get("price", "")),
                            distance=str(poi.get("distance", "")),
                            category=poi.get("category", ""),
                            reviews=poi.get("reviews", [])
                        )
                    collected.append((category_label or normalized_poi.category, normalized_poi))
        
        if not collected:
            for key, pois in poi_map.items():
                if pois:
                    fallback_category = key.partition("_")[2]
                    for poi in pois:
                        normalized_poi = poi
                        if isinstance(poi, dict):
                            normalized_poi = POIInfo(
                                name=poi.get("name", ""),
                                address=poi.get("address", ""),
                                rating=float(poi.get("rating", 0) or 0),
                                business_hours=poi.get("business_hours", "") or poi.get("open_time", ""),
                                price=str(poi.get("price", "")),
                                distance=str(poi.get("distance", "")),
                                category=poi.get("category", ""),
                                reviews=poi.get("reviews", [])
                            )
                        collected.append((fallback_category or normalized_poi.category, normalized_poi))
                    break
        
        return collected
    
    def _is_outdoor_poi(self, poi: POIInfo, category_label: Optional[str]) -> bool:
        """判断POI是否偏户外场景"""
        text = f"{poi.category or ''}{category_label or ''}{poi.name or ''}"
        outdoor_keywords = ["公园", "广场", "景区", "风景", "户外", "古镇", "滨江", "滨水", "步道", "花园", "绿地", "亲水", "动物园", "植物园", "露台", "天台"]
        return any(keyword in text for keyword in outdoor_keywords)
    
    def _is_indoor_poi(self, poi: POIInfo, category_label: Optional[str]) -> bool:
        """判断POI是否偏室内场景"""
        text = f"{poi.category or ''}{category_label or ''}{poi.name or ''}"
        indoor_keywords = ["博物馆", "美术馆", "展览", "购物", "商场", "百货", "餐厅", "咖啡", "KTV", "剧院", "水族馆", "书店", "市集", "体验馆"]
        return any(keyword in text for keyword in indoor_keywords)
    
    def _infer_price_level(self, price_text: str) -> Optional[str]:
        """根据价格信息判断消费档次"""
        if not price_text:
            return None
        matches = re.findall(r'\d+', price_text)
        if not matches:
            return None
        amount = int(matches[0])
        if amount <= 80:
            return "low"
        if amount <= 180:
            return "medium"
        if amount <= 300:
            return "medium_high"
        return "high"
    
    def _score_poi_candidate(self, poi: POIInfo, category_label: Optional[str],
                             weather_analysis: Dict[str, Any],
                             preferences: set,
                             budget_level: Optional[str]) -> Tuple[float, List[str]]:
        """计算POI综合得分及推荐理由"""
        score = 40.0
        reasons: List[str] = []
        
        rating = poi.rating if isinstance(poi.rating, (int, float)) else 0
        if rating and rating > 0:
            score += min(rating * 18, 60)
            reasons.append(f"大众评分 {rating:.1f} 分")
        else:
            reasons.append("口碑信息有限，以现场体验为准")
        
        if self._is_outdoor_poi(poi, category_label):
            reasons.append("户外体验感强")
            if not weather_analysis.get("suitable_for_outdoor", True):
                score -= 25
                reasons.append("当前天气不利于长时间户外，建议作为备选")
            else:
                score += 12
        elif self._is_indoor_poi(poi, category_label):
            reasons.append("室内环境舒适")
            if not weather_analysis.get("suitable_for_outdoor", True):
                score += 18
            else:
                score += 6
        
        preference_labels = {
            "local_culture": "风土人情",
            "local_specialty": "当地特色",
            "off_the_beaten_path": "小众探索",
            "niche": "小众体验",
            "internet_famous": "网红打卡",
            "photo_spots": "拍照",
            "food_focused": "美食",
            "shopping_focused": "购物",
            "history_focused": "历史文化",
            "nature_focused": "自然风光",
            "art_focused": "艺术",
            "nightlife": "夜生活",
            "slow_paced": "慢节奏",
            "in_depth": "深度体验",
            "购物": "购物",
            "美食": "美食",
            "文化": "文化",
            "娱乐": "娱乐",
            "自然": "自然",
            "亲子": "亲子",
            "休闲": "休闲"
        }
        
        poi_text = f"{poi.name or ''}{poi.category or ''}{category_label or ''}"
        for pref in preferences:
            pref_display = preference_labels.get(pref, pref)
            if pref_display and pref_display != pref and pref_display in poi_text:
                score += 10
                reasons.append(f"匹配偏好「{pref_display}」")
            elif pref in poi_text:
                score += 10
                reasons.append(f"匹配偏好「{pref}」")
        
        price_level = self._infer_price_level(poi.price)
        if budget_level and price_level:
            if budget_level == "low" and price_level in ("medium_high", "high"):
                score -= 18
                reasons.append("价格偏高，注意控制预算")
            elif budget_level == "high" and price_level in ("low", "medium"):
                score += 8
                reasons.append("价格亲民，可适当升级体验")
            elif budget_level == price_level:
                score += 6
                reasons.append("价格与预算匹配")
        
        return max(min(score, 100), 0), list(dict.fromkeys(reasons))
    
    def _generate_overall_tips(self, recommendations: List[Dict[str, Any]]) -> List[str]:
        """提炼整体提示"""
        tips: List[str] = []
        
        if not recommendations:
            return ["尚未收集到有效的天气或POI数据，请提醒用户稍后再试。"]
        
        challenging_weather = [
            rec for rec in recommendations
            if rec["weather"].get("condition") in ("extreme", "rainy", "snow") or rec["weather"].get("score", 0) < 55
        ]
        if challenging_weather:
            for rec in challenging_weather:
                tips.append(f"{rec['location']}天气提示：{rec['weather'].get('advice', '请关注天气变化')}。")
        else:
            tips.append("当前整体天气友好，可以安排室内外结合的丰富行程。")
        
        indoor_priority = any(rec.get("indoor_priority") for rec in recommendations)
        if indoor_priority:
            tips.append("为确保体验舒适，建议准备至少一条以室内体验为主的备用路线。")
        
        missing_poi = [rec for rec in recommendations if not rec.get("data_available")]
        if missing_poi:
            tips.append("部分地点暂无权威POI数据，可考虑自行补充当地热门场所。")
        
        return tips
    
    def _format_rag_results(self, rag_data: Dict[str, Any]) -> str:
        """格式化RAG检索结果"""
        if not rag_data or not rag_data.get('results'):
            return "暂无RAG知识库检索结果。"
        
        results = rag_data.get('results', [])
        query = rag_data.get('query', '未知查询')
        
        lines = [f"查询：{query}"]
        lines.append(f"检索到 {len(results)} 条相关知识：\n")
        
        for idx, result in enumerate(results[:5], 1):  # 只显示前5条
            similarity = result.get('similarity', 0)
            # 优先使用text字段，如果没有则尝试从metadata获取
            text = result.get('text', '')
            if not text:
                # 尝试从metadata获取
                meta = result.get('meta', {})
                text = meta.get('text', '') if isinstance(meta, dict) else ''
            
            paragraph_id = result.get('paragraph_id', '')
            source_id = result.get('source_id', '')
            
            # 截断过长的文本
            if len(text) > 200:
                text = text[:200] + "..."
            
            if text:
                lines.append(f"{idx}. [相似度: {similarity:.2f}] {text}")
            else:
                lines.append(f"{idx}. [相似度: {similarity:.2f}] (段落ID: {paragraph_id})")
            
            if source_id and source_id != paragraph_id:
                lines.append(f"   来源: {source_id}")
            elif paragraph_id:
                lines.append(f"   段落ID: {paragraph_id}")
            lines.append("")
        
        return "\n".join(lines)
    
    def _format_analysis_for_prompt(self, analysis: Dict[str, Any]) -> str:
        """将综合分析结果转为文本"""
        if not analysis:
            return "暂无综合分析结果，请提醒补充实时数据。"
        
        lines: List[str] = []
        for rec in analysis.get("locations", []):
            weather = rec.get("weather", {})
            location_name = rec.get("location", "上海")
            lines.append(
                f"- {location_name}：天气 {weather.get('summary', '未知')}，温度 {weather.get('temperature', '未知')}，"
                f"户外适宜：{'是' if weather.get('suitable_for_outdoor') else '否'}。建议：{weather.get('advice', '')}"
            )
            top_pois = rec.get("top_pois", [])
            if top_pois:
                for poi in top_pois[:3]:
                    reason_text = "；".join(poi.get("reasons", [])) if poi.get("reasons") else "综合表现较好"
                    lines.append(
                        f"    · {poi.get('name')}（{poi.get('category') or '未分类'}，综合评分 {poi.get('score')}）—{reason_text}"
                    )
            else:
                lines.append("    · 暂无合适的POI，建议补充相关地点数据。")
        
        overall_tips = analysis.get("overall_tips")
        if overall_tips:
            lines.append("整体提示：" + "；".join(overall_tips))
        
        return "\n".join(lines)
    
    def _parse_tags_from_input(self, user_input: str) -> Dict[str, Any]:
        """解析用户输入中的标签（#标签格式）"""
        import re
        tags = {
            "基础标签": [],
            "偏好标签": [],
            "特殊标签": []
        }
        
        # 匹配 #标签 格式
        tag_pattern = r'#([^\s#]+)'
        found_tags = re.findall(tag_pattern, user_input)
        
        # 基础标签关键词
        basic_keywords = ["天", "晚", "大", "小", "预算", "元", "万", "千", "上海", "北京", "广州"]
        # 偏好标签关键词
        preference_keywords = ["亲子", "情侣", "浪漫", "美食", "购物", "文化", "自然", "避开", "不赶", "必吃", "必去"]
        # 特殊标签关键词
        special_keywords = ["老人", "儿童", "推车", "雨天", "备选", "轮椅", "无障碍"]
        
        for tag in found_tags:
            tag_lower = tag.lower()
            if any(kw in tag for kw in basic_keywords):
                tags["基础标签"].append(tag)
            elif any(kw in tag for kw in preference_keywords):
                tags["偏好标签"].append(tag)
            elif any(kw in tag for kw in special_keywords):
                tags["特殊标签"].append(tag)
            else:
                # 默认归类为偏好标签
                tags["偏好标签"].append(tag)
        
        return tags
    
    def _generate_user_profile(self, extracted_info: Dict[str, Any], tags: Dict[str, Any]) -> Dict[str, Any]:
        """生成用户画像"""
        profile = {
            "出行人群": [],
            "核心偏好": [],
            "限制条件": []
        }
        
        # 解析同伴信息
        companions = extracted_info.get('companions', {})
        if companions.get('type'):
            companion_desc = self._format_companions(companions)
            profile["出行人群"].append(companion_desc)
        
        # 解析预算
        budget_info = extracted_info.get('budget_info', {})
        if budget_info.get('amount'):
            budget_desc = self._format_budget(budget_info)
            profile["限制条件"].append(f"预算：{budget_desc}")
        
        # 解析偏好
        preferences = extracted_info.get('preferences', [])
        if preferences:
            pref_desc = self._format_preferences(preferences)
            profile["核心偏好"].append(pref_desc)
        
        # 从标签中提取信息
        for tag in tags.get("特殊标签", []):
            if "老人" in tag or "65" in tag:
                profile["限制条件"].append("需无障碍设施、电梯景点")
            if "儿童" in tag or "推车" in tag:
                profile["限制条件"].append("儿童推车可通行、避开台阶多的路段")
            if "雨天" in tag:
                profile["限制条件"].append("雨天备选方案")
        
        for tag in tags.get("偏好标签", []):
            if "不赶" in tag or "慢" in tag:
                profile["核心偏好"].append("轻松节奏（日均景点≤3个）")
            if "避开" in tag or "人群" in tag:
                profile["核心偏好"].append("避开人群")
            if "美食" in tag or "本帮菜" in tag:
                profile["核心偏好"].append("本地美食")
        
        return profile
    
    def _generate_final_decision(self, user_input: str, thoughts: List[ThoughtProcess], 
                                extracted_info: Dict[str, Any], real_time_data: Dict[str, Any],
                                context: UserContext) -> str:
        """生成最终决策 - 「知小旅」身份，全流程旅行规划服务"""
        system_prompt = """你是「知小旅」，一个像真人顾问一样懂需求、会变通的智能旅游规划助手。

🎯 你的身份定位：
- 名称固定为「知小旅」，语气亲和自然（如"根据你的情况，我帮你留意了这些细节～"）
- 核心能力：从用户需求出发，完成"需求解码→数据整合→方案生成→交互优化→记忆沉淀"的闭环服务
- 避免机械性回复，要像朋友一样真诚、贴心

💝 回复风格要求：
1. **开头先共情**：理解并表达对用户情感需求的认同
   - 例："和女朋友一起的旅行，确实需要更多浪漫和惊喜呢～"
   - 例："带父母出行最重要的是让他们舒适省心，我特别理解"
   
2. **用词温暖自然**：
   - 多用"你"、"咱们"、"我帮你留意了"
   - 避免生硬的"应该"、"必须"
   - 用"～"、"呢"、"哦"等语气词增加亲和力
   - 使用"知小旅"自称，不要说"我是AI"或"我是系统"
   
3. **加入情感细节**：
   - 推荐景点时说明"为什么适合你们"
   - 分享小故事或本地人的秘密
   - 给出温馨提示时解释背后的原因
   
4. **体现专业温度**：
   - 基于数据，但用人话表达
   - 例：不说"人流密度中等"，而说"这时候人不算多，逛起来会比较舒服"

🎯 核心原则：
1. **深度理解需求**：
   - 显性需求：时间、人数、目的地、预算、核心诉求
   - 隐性需求：根据标签/描述挖掘潜在需求（如#带老人→优先电梯景点/午休1.5小时；#儿童推车→避开台阶多的路段）
   - 冲突协调：若需求矛盾（如"预算有限+住迪士尼酒店"），需主动提示并提供折中方案
   
2. **严格尊重用户偏好**：
   - "避开人群"→推荐小众安静的地方
   - "想要浪漫"→避开过于商业的景点
   - "地道体验"→推荐本地人常去的地方
   
3. **预算敏感度**：
   - 经济型：强调性价比，推荐免费景点和平价美食
   - 高端型：推荐特色体验和品质餐厅
   
4. **真诚实用**：
   - 基于实时数据，不编造信息
   - 给出具体的时间、地址、价格
   - 分享实用的避坑tips

5. **必须反馈的要点**：
   - 无论用户是否提及，都要明确说明天气状况（含温度、对户外活动的影响）
   - 无论用户是否提及，都要提供至少3个核心POI或体验的推荐理由
   - 若实时数据缺失，需诚实告知并给出替代建议

📝 输出结构要求（必须包含以下内容）：
1. **行程主题**：一句话概括（如"上海4天亲子慢游：经典地标+轻松体验，兼顾老人舒适"）
2. **行程总览**：含天数、总预算、室内/室外占比、核心亮点
3. **每日细化行程**：
   - 时间轴：精确到30分钟（如"09:30-11:00 外滩漫步（户外）→11:00-11:30 休息区补给→11:30-13:00 餐厅用餐（室内）"）
   - 细节标注：步行距离、儿童友好提示、老人便利信息
4. **备选方案库**：每个核心节点提供2个备选，附替换理由+优劣势对比
5. **实用工具箱**：
   - 天气提醒：按天标注穿衣建议
   - 预约指南：附各景点/餐厅预约入口+操作步骤
   - 物品清单：按人群分类

请用充满人情味的方式，生成让用户感到被理解、被关心的旅游攻略。记住：你是「知小旅」，一个热爱上海、懂得生活的本地朋友。"""
        
        # 构建思考过程摘要
        thoughts_summary = "\n".join([
            f"步骤{t.step}: {t.thought} - {t.reasoning}"
            for t in thoughts
        ])
        
        # 转换数据为可序列化格式
        recommendation_analysis = self._build_environmental_recommendations(extracted_info, real_time_data, context)
        real_time_data["analysis"] = recommendation_analysis
        
        serializable_data = self._convert_to_serializable(real_time_data)
        
        # 构建人文信息摘要
        human_factors = []
        
        if extracted_info.get('user_intent_summary'):
            human_factors.append(f"需求理解：{extracted_info['user_intent_summary']}")
        
        if extracted_info.get('companions') and extracted_info['companions']['type']:
            companion_desc = self._format_companions(extracted_info['companions'])
            human_factors.append(f"同伴：{companion_desc}")
            
            # 根据同伴类型添加特殊提示
            companion_type = extracted_info['companions']['type']
            if companion_type == 'romantic_partner':
                human_factors.append("💝 特别注意：这是一次浪漫之旅，请推荐适合情侣的浪漫景点和餐厅")
            elif companion_type == 'family':
                human_factors.append("👨‍👩‍👧‍👦 特别注意：这是家庭出游，请考虑便捷性和全家人都适合的活动")
            elif companion_type == 'friends':
                human_factors.append("👫 特别注意：这是朋友聚会，可以推荐有趣、热闹的地方")
        
        if extracted_info.get('emotional_context'):
            emotional_desc = self._format_emotional_context(extracted_info['emotional_context'])
            if emotional_desc:
                human_factors.append(f"情感需求：{emotional_desc}")
        
        if extracted_info.get('budget_info') and extracted_info['budget_info']['amount']:
            budget_desc = self._format_budget(extracted_info['budget_info'])
            human_factors.append(f"预算：{budget_desc}")
        
        if extracted_info.get('preferences'):
            pref_desc = self._format_preferences(extracted_info['preferences'])
            human_factors.append(f"特殊偏好：{pref_desc}")
        
        human_factors_text = "\n- ".join(human_factors) if human_factors else "无特殊要求"
        
        # 格式化RAG结果
        rag_text = self._format_rag_results(real_time_data.get('rag', {}))
        
        # 格式化用户画像
        user_profile = extracted_info.get('user_profile', {})
        profile_text = ""
        if user_profile:
            profile_text = "【用户画像】\n"
            if user_profile.get("出行人群"):
                profile_text += f"出行人群：{', '.join(user_profile['出行人群'])}\n"
            if user_profile.get("核心偏好"):
                profile_text += f"核心偏好：{', '.join(user_profile['核心偏好'])}\n"
            if user_profile.get("限制条件"):
                profile_text += f"限制条件：{', '.join(user_profile['限制条件'])}\n"
        
        # 格式化标签信息
        tags = extracted_info.get('tags', {})
        tags_text = ""
        if any(tags.values()):
            tags_text = "【标签信息】\n"
            if tags.get("基础标签"):
                tags_text += f"基础标签：{', '.join([f'#{t}' for t in tags['基础标签']])}\n"
            if tags.get("偏好标签"):
                tags_text += f"偏好标签：{', '.join([f'#{t}' for t in tags['偏好标签']])}\n"
            if tags.get("特殊标签"):
                tags_text += f"特殊标签：{', '.join([f'#{t}' for t in tags['特殊标签']])}\n"
        
        user_message = f"""用户需求：{user_input}

{tags_text}
{profile_text}

【第一步：Agent思考链】
我的思考过程：
{thoughts_summary}

【第二步：分词提取的关键信息】
- 地点关键词：{', '.join(extracted_info.get('tokenized_data', {}).get('location_keywords', [])[:5]) if extracted_info.get('tokenized_data') else '未提取'}
- 时间关键词：{', '.join(extracted_info.get('tokenized_data', {}).get('time_keywords', [])[:5]) if extracted_info.get('tokenized_data') else '未提取'}
- 活动关键词：{', '.join(extracted_info.get('tokenized_data', {}).get('activity_keywords', [])[:5]) if extracted_info.get('tokenized_data') else '未提取'}

【重要】人文因素分析（请特别关注）：
- {human_factors_text}

基础信息：
- 旅行天数：{extracted_info['travel_days']}天
- 地点：{', '.join(extracted_info['locations']) if extracted_info['locations'] else '未指定'}
- 活动类型：{', '.join(extracted_info['activity_types']) if extracted_info['activity_types'] else '未指定'}

【第三步：MCP实时数据】
{json.dumps(serializable_data, ensure_ascii=False, indent=2)}

【第四步：RAG知识库检索结果】
{rag_text}

请基于以上所有信息（Agent思考链、分词结果、MCP实时数据、RAG知识库信息），生成第一版旅游攻略方案。

⚠️ **重要约束：避免重复规划**
1. **严禁重复推荐**：同一个景点/餐厅在多天行程中最多只能出现1次，除非用户明确要求重复游览
2. **每天不同主题**：每天的行程应该有不同的主题和重点，避免雷同
3. **景点多样性**：确保每天推荐的景点、餐厅、活动都不相同
4. **检查清单**：生成方案前，请检查是否有多天重复同一个地点的情况，如有请立即调整

📋 输出格式要求（必须严格按照以下结构，使用Markdown格式）：

1. **行程主题**（第一行，加粗，必须）
   - 格式：**行程主题：** [一句话概括，如"上海4天亲子慢游：经典地标+轻松体验，兼顾老人舒适"]

2. **行程总览**（结构化展示，必须）
   ```
   天数：[X]天
   总预算：约¥[金额]
   室内/室外占比：[X]%室内 + [Y]%室外
   核心亮点：
   • [亮点1]
   • [亮点2]
   • [亮点3]
   ```

3. **每日细化行程**（按天分段，精确到30分钟，必须）
   - 格式示例：
     **第1天：[日期]**
     
     **09:30-11:00** 外滩漫步
     - 类型：户外景点
     - 位置：黄浦区中山东一路
     - 距离：约800米，平坦无台阶
     - 👶 儿童友好：有母婴室
     - 👴 老人便利：可租轮椅
     - 💡 推荐理由：[为什么推荐这里]
     
     **11:00-11:30** 休息区补给
     - 位置：[具体位置]
     
     **11:30-13:00** 餐厅用餐
     - 餐厅：[餐厅名]
     - 位置：[地址]
     - 类型：室内
     - 💰 人均消费：约¥[金额]

4. **备选方案库**（每个核心节点提供2个备选，可选）
   - 格式：
     **备选方案：**
     - 若遇雨天，外滩替换为上海历史博物馆
       理由：室内避雨，但互动性稍弱
       优势：完全避雨，有丰富展品
       劣势：缺少户外体验

5. **实用工具箱**
   - **天气提醒**：按天标注穿衣建议（如"11月22日10-15℃，建议老人穿羽绒服+防滑鞋"）
   - **预约指南**：附各景点/餐厅预约入口+操作步骤+最佳预约时间
   - **物品清单**：按人群分类（儿童：推车、保温杯；老人：降压药、折叠凳）

特别提醒：
1. **严格限制地区**：只推荐上海地区的景点、餐厅、商店等，绝对不要推荐北京、广州、深圳等其他城市的任何地点。
2. **过滤非上海内容**：在生成回复前，请仔细检查所有推荐的地点，确保它们都在上海。
3. 必须在攻略中体现对同伴关系的关注（如：女朋友、父母等）
4. 必须根据情感需求调整推荐（如：浪漫氛围、避开人群等）
5. 必须考虑预算档次来推荐合适的消费场所
6. 在攻略开头简要说明你的思考逻辑和对用户需求的理解
7. 充分利用RAG知识库中的相关信息，提供更专业、更地道的建议
8. **重要**：如果推荐的地点中包含"北京"字样，请确认是上海的"北京东路"或"北京西路"等街道，而不是北京市的景点。
9. **反馈引导**：在方案结尾添加："这份行程是否符合你的预期？可选择：①满意 ②不满意（请说明具体调整点）"
10. **重复检查**：生成方案后，请自我检查：
    - 是否有同一个景点在多天出现？如有，请替换为其他景点
    - 是否有同一个餐厅在多天出现？如有，请替换为其他餐厅
    - 每天的行程主题是否不同？如相同，请调整主题和景点选择
    - 确保每天都有新的体验和不同的地点 """
        
        if recommendation_analysis:
            analysis_text = self._format_analysis_for_prompt(recommendation_analysis)
            user_message += f"\n附加分析：\n{analysis_text}\n"
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]
        
        response = self.doubao_agent.generate_response(messages)
        
        # 后处理：过滤掉回复中可能出现的非上海地区推荐
        response = self._filter_response_for_shanghai_only(response)
        
        # 后处理：检查并修复重复规划问题
        response = self._check_and_fix_duplicates(response, extracted_info)
        
        return response
    
    def _filter_response_for_shanghai_only(self, response: str) -> str:
        """过滤回复中的非上海地区推荐"""
        if not response:
            return response
        
        # 非上海城市关键词（排除上海的街道名）
        non_shanghai_cities = [
            "北京", "广州", "深圳", "杭州", "南京", "苏州", "成都", "重庆",
            "西安", "武汉", "天津", "长沙", "郑州", "济南", "青岛", "大连",
            "厦门", "福州", "合肥", "南昌", "石家庄", "太原", "哈尔滨", "长春",
            "沈阳", "昆明", "贵阳", "南宁", "海口", "乌鲁木齐", "拉萨", "银川",
            "西宁", "兰州", "呼和浩特"
        ]
        
        # 上海的街道名（这些应该保留）
        shanghai_streets = [
            "北京东路", "北京西路", "南京东路", "南京西路", "淮海东路", "淮海西路",
            "中山北路", "中山南路", "中山中路", "中山东路", "延安东路", "延安西路",
            "延安中路", "四川北路", "四川南路", "四川中路"
        ]
        
        lines = response.split('\n')
        filtered_lines = []
        
        for line in lines:
            # 检查是否包含非上海城市关键词
            should_remove = False
            
            for city in non_shanghai_cities:
                if city in line:
                    # 检查是否是上海的街道名
                    is_shanghai_street = any(street in line for street in shanghai_streets)
                    if not is_shanghai_street:
                        # 检查是否是推荐行（包含"推荐"、"建议"、"可以去"等）
                        if any(keyword in line for keyword in ["推荐", "建议", "可以去", "值得", "位于", "在", "位于北京", "位于广州", "位于深圳"]):
                            should_remove = True
                            logger.warning(f"过滤回复中的非上海推荐: {line[:50]}...")
                            break
            
            if not should_remove:
                filtered_lines.append(line)
        
        if len(filtered_lines) < len(lines):
            logger.info(f"回复过滤: 原始{len(lines)}行，过滤后{len(filtered_lines)}行（已删除{len(lines) - len(filtered_lines)}行非上海推荐）")
        
        return '\n'.join(filtered_lines)
    
    def _check_and_fix_duplicates(self, response: str, extracted_info: Dict[str, Any]) -> str:
        """检查并修复行程中的重复规划问题"""
        if not response:
            return response
        
        import re
        
        # 提取所有提到的地点
        lines = response.split('\n')
        mentioned_places = {}
        day_pattern = re.compile(r'第(\d+)天|Day\s*(\d+)', re.IGNORECASE)
        place_pattern = re.compile(r'前往([^（(]+)|([^（(]+)（', re.IGNORECASE)
        restaurant_pattern = re.compile(r'餐厅[用餐]?[：:]\s*([^，,。\n]+)', re.IGNORECASE)
        
        current_day = None
        duplicates_found = []
        
        for i, line in enumerate(lines):
            # 检测天数
            day_match = day_pattern.search(line)
            if day_match:
                current_day = int(day_match.group(1) or day_match.group(2))
                continue
            
            if current_day is None:
                continue
            
            # 检测景点
            place_match = place_pattern.search(line)
            if place_match:
                place = (place_match.group(1) or place_match.group(2)).strip()
                if place and len(place) > 2:  # 过滤太短的匹配
                    place = place.replace('前往', '').replace('前往', '').strip()
                    if place in mentioned_places:
                        duplicates_found.append((current_day, place, mentioned_places[place]))
                    else:
                        mentioned_places[place] = current_day
            
            # 检测餐厅
            restaurant_match = restaurant_pattern.search(line)
            if restaurant_match:
                restaurant = restaurant_match.group(1).strip()
                if restaurant and len(restaurant) > 2:
                    if restaurant in mentioned_places:
                        duplicates_found.append((current_day, restaurant, mentioned_places[restaurant]))
                    else:
                        mentioned_places[restaurant] = current_day
        
        # 如果发现重复，添加警告提示
        if duplicates_found:
            warning = "\n\n⚠️ **检测到重复规划问题**：\n"
            for day, place, first_day in duplicates_found:
                warning += f"- 第{day}天和第{first_day}天都安排了「{place}」，建议替换为其他地点\n"
            warning += "\n请知小旅重新规划，确保每天都有不同的景点和餐厅。\n"
            
            # 在回复末尾添加警告
            if "这份行程是否符合你的预期" not in response:
                response += warning
            else:
                # 在反馈引导前插入警告
                response = response.replace(
                    "这份行程是否符合你的预期",
                    warning + "这份行程是否符合你的预期"
                )
            
            logger.warning(f"检测到重复规划：{duplicates_found}")
        
        return response
    
    def _update_user_memory(self, context: UserContext, extracted_info: Dict[str, Any], tags: Dict[str, Any]):
        """更新用户记忆，沉淀稳定偏好"""
        memory = context.user_memory
        
        # 记录最近的偏好选择
        recent_preferences = []
        
        # 从extracted_info中提取偏好
        if extracted_info.get('preferences'):
            recent_preferences.extend(extracted_info['preferences'])
        
        if extracted_info.get('companions') and extracted_info['companions'].get('type'):
            recent_preferences.append(f"companion_{extracted_info['companions']['type']}")
        
        if extracted_info.get('budget_info') and extracted_info['budget_info'].get('level'):
            recent_preferences.append(f"budget_{extracted_info['budget_info']['level']}")
        
        # 从标签中提取偏好
        for tag_list in tags.values():
            for tag in tag_list:
                recent_preferences.append(f"tag_{tag}")
        
        # 更新最近选择（保留最近10次）
        memory['recent_choices'].extend(recent_preferences)
        memory['recent_choices'] = memory['recent_choices'][-10:]
        
        # 统计偏好出现次数，如果>=3次则加入稳定偏好
        from collections import Counter
        preference_counts = Counter(memory['recent_choices'])
        
        for pref, count in preference_counts.items():
            if count >= 3 and pref not in memory['stable_preferences']:
                memory['stable_preferences'][pref] = count
                logger.info(f"记录稳定偏好: {pref} (出现{count}次)")
    
    # ==================== 原有方法（保留向后兼容） ====================
    
    def _generate_initial_response(self, user_input: str, context: UserContext) -> str:
        """让豆包Agent生成初始回复，理解用户需求"""
        print("🤖 Agent正在理解您的需求...")
        
        system_prompt = """你是一个专业的上海旅游规划师。请理解用户的需求并生成初步的旅游建议。

要求：
1. 只推荐上海地区的景点和地点
2. 不要推荐北京、广州等其他城市的景点
3. 根据用户的具体需求给出建议
4. 如果用户提到特定区域（如普陀区），请推荐该区域及周边的景点

请生成简洁的初步建议，后续会根据实时数据优化。"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input}
        ]
        
        return self.doubao_agent.generate_response(messages)
    
    def _analyze_agent_response_for_mcp(self, agent_response: str, user_input: str) -> List[MCPServiceType]:
        """根据Agent的回复分析需要哪些MCP服务"""
        required_services = []
        
        # 对于旅游攻略，默认需要所有核心MCP服务
        required_services = [
            MCPServiceType.WEATHER,    # 天气信息
            MCPServiceType.POI,        # 景点和餐厅信息
            MCPServiceType.TRAFFIC,    # 路况信息
            MCPServiceType.NAVIGATION, # 导航路线
            MCPServiceType.CROWD       # 人流信息
        ]
        
        # 根据用户具体需求调整
        if "天气" not in user_input and "下雨" not in user_input and "晴天" not in user_input:
            # 如果用户没有明确询问天气，但需要做攻略，仍然需要天气信息
            pass  # 保留天气服务
        
        if "交通" not in user_input and "路线" not in user_input:
            # 如果用户没有明确询问交通，但需要做攻略，仍然需要导航信息
            pass  # 保留导航服务
        
        return required_services
    
    def _call_targeted_mcp_services(self, required_services: List[MCPServiceType], user_input: str, context: UserContext) -> Dict[str, Any]:
        """调用目标MCP服务"""
        print("📡 Agent正在收集实时数据来优化您的攻略...")
        real_time_data = {}
        
        # 从用户输入中提取具体地点和路线信息
        extracted_locations = self._extract_locations_from_input(user_input)
        route_info = self._extract_route_from_input(user_input)
        
        # 按正确顺序调用MCP服务
        for service in required_services:
            try:
                # 使用MCP客户端统一调用服务
                if service == MCPServiceType.WEATHER:
                    weather_data = {}
                    locations = extracted_locations if extracted_locations else ["上海"]
                    for location in locations:
                        weather = self.mcp_client.call_service(
                            MCPServiceType.WEATHER,
                            city=location,
                            date=context.travel_preferences.start_date
                        )
                        weather_data[location] = weather
                    real_time_data["weather"] = weather_data
                
                elif service == MCPServiceType.POI:
                    poi_data = {}
                    try:
                        locations = extracted_locations if extracted_locations else ["上海"]
                        for location in locations:
                            attractions = self.mcp_client.call_service(
                                MCPServiceType.POI,
                                keyword="景点",
                                city=location,
                                category="110000"
                            )
                            poi_data[f"{location}_景点"] = attractions
                            
                            restaurants = self.mcp_client.call_service(
                                MCPServiceType.POI,
                                keyword="餐厅",
                                city=location,
                                category="050000"
                            )
                            poi_data[f"{location}_餐饮"] = restaurants
                    except Exception as e:
                        logger.error(f"POI服务调用失败: {e}")
                    real_time_data["poi"] = poi_data
                
                elif service == MCPServiceType.NAVIGATION:
                    navigation_data = {}
                    if route_info:
                        start = route_info["start"]
                        end = route_info["end"]
                        routes = self.mcp_client.call_service(
                            MCPServiceType.NAVIGATION,
                            origin=start,
                            destination=end
                        )
                        navigation_data[f"{start}_to_{end}"] = routes
                        real_time_data["_route_info"] = route_info
                    elif len(extracted_locations) >= 2:
                        for i in range(len(extracted_locations) - 1):
                            start = extracted_locations[i]
                            end = extracted_locations[i + 1]
                            routes = self.mcp_client.call_service(
                                MCPServiceType.NAVIGATION,
                                origin=start,
                                destination=end
                            )
                            navigation_data[f"{start}_to_{end}"] = routes
                    real_time_data["navigation"] = navigation_data
                
                elif service == MCPServiceType.TRAFFIC:
                    traffic_data = {}
                    if "_route_info" in real_time_data:
                        route_info = real_time_data["_route_info"]
                        start = route_info["start"]
                        end = route_info["end"]
                        traffic_start = self.mcp_client.call_service(MCPServiceType.TRAFFIC, area=start)
                        traffic_end = self.mcp_client.call_service(MCPServiceType.TRAFFIC, area=end)
                        traffic_data[f"{start}_to_{end}"] = {
                            "start_location": traffic_start,
                            "end_location": traffic_end
                        }
                    elif extracted_locations:
                        for location in extracted_locations:
                            traffic = self.mcp_client.call_service(MCPServiceType.TRAFFIC, area=location)
                            traffic_data[location] = traffic
                    else:
                        traffic = self.mcp_client.call_service(MCPServiceType.TRAFFIC, area="上海")
                        traffic_data["上海"] = traffic
                    real_time_data["traffic"] = traffic_data
                
                elif service == MCPServiceType.CROWD:
                    crowd_data = {}
                    locations = extracted_locations if extracted_locations else ["上海"]
                    for location in locations:
                        crowd = self.mcp_client.call_service(MCPServiceType.CROWD, location=location)
                        crowd_data[location] = crowd
                    real_time_data["crowd"] = crowd_data
                
            except Exception as e:
                logger.error(f"MCP服务 {service.value} 调用失败: {e}")
                real_time_data[service.value] = {"error": str(e)}
        
        return real_time_data
    
    def _optimize_response_with_data(self, user_input: str, initial_response: str, real_time_data: Dict[str, Any], context: UserContext) -> str:
        """使用实时数据优化Agent的回复"""
        print("🤖 Agent正在思考并优化您的旅游攻略...")
        
        system_prompt = """你是一个专业、温暖、贴心的上海旅游规划师。请基于用户的初始需求和实时数据，生成科学、详细、富有人情味的旅游攻略。

你的特点：
1. 专业：基于实时数据（天气、路况、人流、POI）制定科学合理的行程
2. 贴心：考虑用户的具体需求（如不喜欢人多、想要浪漫氛围等）
3. 详细：提供具体的地址、交通方式、时间安排、费用预算
4. 人性化：用温暖的语言，给出实用的建议和温馨提示

重要要求：
1. 严格基于提供的实时数据生成回复，不要编造信息
2. 只推荐上海地区的景点和地点
3. 根据实时天气调整室内外活动安排
4. 根据路况信息优化交通路线
5. 根据人流信息推荐最佳游览时间
6. 提供具体的地址、交通方式、费用预算
7. 给出贴心的温馨提示和注意事项
8. 请务必在回复中明确说明天气状况（含温度及其对行程的影响）以及核心POI推荐理由；若数据缺失，需要如实告知并提供备选建议

请生成详细、实用、富有人情味的旅游攻略。"""
        
        # 将POIInfo对象转换为可序列化的字典
        serializable_data = self._convert_to_serializable(real_time_data)
        
        user_message = f"""用户需求：{user_input}

初始建议：{initial_response}

实时数据：
{json.dumps(serializable_data, ensure_ascii=False, indent=2)}

请基于以上信息，生成优化的旅游攻略。"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]
        
        return self.doubao_agent.generate_response(messages)
    
    def _convert_to_serializable(self, data: Any) -> Any:
        """将数据转换为可JSON序列化的格式"""
        if isinstance(data, dict):
            return {key: self._convert_to_serializable(value) for key, value in data.items()}
        elif isinstance(data, list):
            return [self._convert_to_serializable(item) for item in data]
        elif hasattr(data, '__dict__'):
            # 处理POIInfo等自定义对象
            if hasattr(data, 'name'):
                # POIInfo对象
                return {
                    "name": data.name,
                    "address": data.address,
                    "rating": data.rating,
                    "business_hours": data.business_hours,
                    "price": data.price,
                    "distance": data.distance,
                    "category": data.category,
                    "reviews": data.reviews
                }
            elif hasattr(data, 'weather'):
                # WeatherInfo对象
                return {
                    "date": data.date,
                    "weather": data.weather,
                    "temperature": data.temperature,
                    "wind": data.wind,
                    "humidity": data.humidity,
                    "precipitation": data.precipitation
                }
            else:
                return str(data)
        else:
            return data
    
    def _start_thinking_process(self, user_input: str, context: UserContext) -> List[ThoughtProcess]:
        """开始思考联想过程"""
        thoughts = []
        step = 1
        
        logger.info("🧠 开始深度思考联想过程...")
        
        # 第一步：深度理解用户需求
        detected_locations, activity_types = self._analyze_user_intent(user_input)
        travel_days = self._extract_travel_days(user_input)
        
        thought1 = ThoughtProcess(
            step=step,
            thought="深度理解用户的核心需求",
            keywords=self._extract_keywords(user_input) + [f"{travel_days}天"],
            mcp_services=[],
            reasoning=f"用户需要{travel_days}天的上海旅游攻略，需要全面考虑时间安排、景点分布、交通规划等",
            timestamp=datetime.now().isoformat()
        )
        thoughts.append(thought1)
        step += 1
        
        # 第二步：智能景点推荐策略
        if not detected_locations:
            thought2 = ThoughtProcess(
                step=step,
                thought="智能推荐上海经典景点",
                keywords=["上海经典景点", "三日游"],
                mcp_services=[MCPServiceType.POI],
                reasoning=f"用户需要{travel_days}天攻略但未指定地点，需要推荐上海经典景点组合",
                timestamp=datetime.now().isoformat()
            )
            thoughts.append(thought2)
            step += 1
        else:
            thought2 = ThoughtProcess(
                step=step,
                thought="分析指定景点的周边推荐",
                keywords=detected_locations + activity_types,
                mcp_services=[MCPServiceType.POI],
                reasoning=f"用户指定了{detected_locations}，需要推荐周边相关景点",
                timestamp=datetime.now().isoformat()
            )
            thoughts.append(thought2)
            step += 1
        
        # 第三步：多日天气规划
        if travel_days > 1:
            thought3 = ThoughtProcess(
                step=step,
                thought="多日天气规划策略",
                keywords=["多日天气", "行程调整"],
                mcp_services=[MCPServiceType.WEATHER],
                reasoning=f"需要规划{travel_days}天的行程，必须考虑每天的天气情况来合理安排室内外活动",
                timestamp=datetime.now().isoformat()
            )
            thoughts.append(thought3)
            step += 1
        else:
            thought3 = ThoughtProcess(
                step=step,
                thought="单日天气检查",
                keywords=["天气", "温度", "降水"],
                mcp_services=[MCPServiceType.WEATHER],
                reasoning="单日行程需要检查天气状况以确保行程合理性",
                timestamp=datetime.now().isoformat()
            )
            thoughts.append(thought3)
            step += 1
        
        # 第四步：多日交通路线规划
        if travel_days > 1:
            thought4 = ThoughtProcess(
                step=step,
                thought="多日交通路线规划",
                keywords=["多日路线", "交通规划"],
                mcp_services=[MCPServiceType.NAVIGATION],
                reasoning=f"需要规划{travel_days}天的交通路线，考虑景点间的距离和交通方式",
                timestamp=datetime.now().isoformat()
            )
            thoughts.append(thought4)
            step += 1
        else:
            thought4 = ThoughtProcess(
                step=step,
                thought="单日交通路线规划",
                keywords=["路线", "交通", "导航"],
                mcp_services=[MCPServiceType.NAVIGATION],
                reasoning="需要规划单日最优交通路线",
                timestamp=datetime.now().isoformat()
            )
            thoughts.append(thought4)
            step += 1
        
        # 第五步：路况和交通优化
        thought5 = ThoughtProcess(
            step=step,
            thought="路况分析和交通优化",
            keywords=["路况", "拥堵", "交通"],
            mcp_services=[MCPServiceType.TRAFFIC],
            reasoning="需要检查实时路况，为交通规划提供优化建议",
            timestamp=datetime.now().isoformat()
        )
        thoughts.append(thought5)
        step += 1
        
        # 第六步：人流分析和时间优化
        thought6 = ThoughtProcess(
            step=step,
            thought="人流分析和时间优化",
            keywords=["人流", "拥挤", "排队", "时间优化"],
            mcp_services=[MCPServiceType.CROWD],
            reasoning="需要分析各景点的人流情况，合理安排游览时间，避开高峰期",
            timestamp=datetime.now().isoformat()
        )
        thoughts.append(thought6)
        step += 1
        
        # 第七步：综合评估和多日规划
        thought7 = ThoughtProcess(
            step=step,
            thought="综合评估和多日旅游规划",
            keywords=["综合评估", "多日规划", "个性化推荐"],
            mcp_services=[MCPServiceType.WEATHER, MCPServiceType.NAVIGATION, MCPServiceType.TRAFFIC, MCPServiceType.POI, MCPServiceType.CROWD],
            reasoning=f"整合所有信息，生成{travel_days}天的科学合理旅游攻略，包含每日安排、交通建议、天气应对等",
            timestamp=datetime.now().isoformat()
        )
        thoughts.append(thought7)
        
        logger.info(f"🧠 深度思考过程完成，共 {len(thoughts)} 个步骤")
        
        return thoughts
    
    def _collect_real_time_data(self, thoughts: List[ThoughtProcess], user_input: str, context: UserContext) -> Dict[str, Any]:
        """收集实时数据"""
        logger.info("📡 收集实时数据...")
        
        # 收集需要调用的MCP服务
        required_services = set()
        for thought in thoughts:
            required_services.update(thought.mcp_services)
        
        # 执行MCP服务调用
        real_time_data = {}
        
        # 提取目的地和起点
        detected_locations, _ = self._analyze_user_intent(user_input)
        travel_days = self._extract_travel_days(user_input)
        
        # 从用户输入中提取具体地点
        extracted_locations = self._extract_locations_from_input(user_input)
        if extracted_locations:
            destinations = extracted_locations
        else:
            destinations = detected_locations if detected_locations else ["外滩"]  # 默认目的地
        
        origin = "人民广场"  # 默认起点
        
        for service in required_services:
            try:
                if service == MCPServiceType.WEATHER:
                    logger.info("🌤️ 调用天气服务")
                    weather_data = {}
                    for dest in destinations:
                        weather_info = self.get_weather(dest, context.travel_preferences.start_date)
                        weather_data[dest] = weather_info
                    real_time_data["weather"] = weather_data
                
                elif service == MCPServiceType.NAVIGATION:
                    logger.info("🗺️ 调用导航服务")
                    if len(destinations) > 1:
                        nav_results = []
                        for i in range(len(destinations) - 1):
                            route = self.get_navigation_routes(destinations[i], destinations[i+1])
                            nav_results.append(route)
                        real_time_data["navigation"] = nav_results
                    else:
                        route = self.get_navigation_routes(origin, destinations[0])
                        real_time_data["navigation"] = [route]
                
                elif service == MCPServiceType.TRAFFIC:
                    logger.info("🚦 调用路况服务")
                    traffic_data = {}
                    
                    # 根据用户输入判断是否需要调用路况服务
                    if "交通" in user_input or "路况" in user_input or "堵车" in user_input:
                        for dest in destinations:
                            logger.info(f"调用路况API获取实时数据: {dest}")
                            traffic_info = self.get_traffic_status(dest)
                            traffic_data[dest] = traffic_info
                    else:
                        # 如果用户没有明确询问交通，只获取主要目的地的路况
                        if destinations:
                            main_dest = destinations[0]
                            logger.info(f"调用路况API获取实时数据: {main_dest}")
                            traffic_info = self.get_traffic_status(main_dest)
                            traffic_data[main_dest] = traffic_info
                    
                    real_time_data["traffic"] = traffic_data
                
                elif service == MCPServiceType.POI:
                    logger.info("🔍 调用POI服务")
                    poi_data = {}
                    
                    # 简化POI搜索逻辑，让豆包Agent来决定如何使用这些数据
                    if not destinations:
                        # 搜索上海的主要景点和商圈
                        attractions = self.search_poi("景点", "上海", "110000")
                        poi_data["上海景点"] = attractions
                        
                        restaurants = self.search_poi("餐厅", "上海", "050000")
                        poi_data["上海餐饮"] = restaurants
                        
                        shopping_areas = self.search_poi("商圈", "上海", "060000")
                        poi_data["上海商圈"] = shopping_areas
                    else:
                        for dest in destinations:
                            attractions = self.search_poi("景点", dest, "110000")
                            poi_data[f"{dest}_景点"] = attractions
                            
                            restaurants = self.search_poi("餐厅", dest, "050000")
                            poi_data[f"{dest}_餐饮"] = restaurants
                    
                    real_time_data["poi"] = poi_data
                
                elif service == MCPServiceType.CROWD:
                    logger.info("👥 调用人流服务")
                    crowd_data = {}
                    for dest in destinations:
                        crowd_data[dest] = {
                            "level": "moderate",
                            "description": "人流适中",
                            "recommendation": "适合游览"
                        }
                    real_time_data["crowd"] = crowd_data
                
            except Exception as e:
                logger.error(f"MCP服务 {service.value} 调用失败: {e}")
                real_time_data[service.value] = {"error": str(e)}
        
        return real_time_data
    
    def _generate_response_with_doubao(self, user_input: str, real_time_data: Dict[str, Any], context: UserContext) -> str:
        """使用豆包Agent生成回复"""
        logger.info("🤖 使用豆包Agent生成回复...")
        
        # 构建系统提示词
        system_prompt = self._build_system_prompt(real_time_data, context)
        
        # 构建用户消息
        user_message = self._build_user_message(user_input, real_time_data)
        
        # 调用豆包Agent
        messages = [
            {"role": "user", "content": user_message}
        ]
        
        response = self.doubao_agent.generate_response(messages, system_prompt)
        
        return response
    
    def _build_system_prompt(self, real_time_data: Dict[str, Any], context: UserContext) -> str:
        """构建系统提示词"""
        prompt = """你是一个专业的上海旅游攻略规划师，具备以下能力：
1. 深度理解用户需求，提供个性化的旅游建议
2. 基于实时数据（天气、交通、人流、POI）制定科学合理的行程
3. 考虑多日游的时间安排和景点分布
4. 提供实用的交通建议和注意事项

重要要求：
- 严格基于提供的实时数据生成回复
- 只推荐上海地区的景点和地点，不要推荐北京、广州等其他城市的景点
- 如果用户询问特定地点的交通情况，请重点回答该地点的路况信息
- 所有推荐的地点必须是上海地区的
- 必须使用提供的实时数据，不要编造信息
- 无论用户是否提及，都要明确说明天气状况（含温度及对行程的影响）和核心POI推荐理由
- 若缺少相关数据，需要坦诚告知并提供替代建议

请根据提供的实时数据，为用户生成详细、实用的旅游攻略。"""
        
        return prompt
    
    def _build_user_message(self, user_input: str, real_time_data: Dict[str, Any]) -> str:
        """构建用户消息"""
        message = f"用户需求：{user_input}\n\n"
        
        # 添加实时数据
        if real_time_data:
            message += "实时数据：\n"
            
            if "weather" in real_time_data:
                weather_info = real_time_data["weather"]
                message += "🌤️ 天气信息：\n"
                for location, weather in weather_info.items():
                    if weather and len(weather) > 0:
                        weather_data = weather[0] if isinstance(weather, list) else weather
                        message += f"  {location}：{weather_data.weather}，{weather_data.temperature}\n"
                    else:
                        message += f"  {location}：暂无实时天气数据\n"
            else:
                message += "🌤️ 天气信息：暂无实时数据，请提醒用户关注临近天气预报。\n"
            
            if "poi" in real_time_data:
                poi_info = real_time_data["poi"]
                message += "🎯 景点信息：\n"
                for category, pois in poi_info.items():
                    if pois and len(pois) > 0:
                        message += f"  {category}：\n"
                        for poi in pois[:3]:
                            poi_name = getattr(poi, "name", None)
                            poi_rating = getattr(poi, "rating", None)
                            if poi_name is None and isinstance(poi, dict):
                                poi_name = poi.get("name")
                            if poi_rating is None and isinstance(poi, dict):
                                poi_rating = poi.get("rating")
                            if poi_name and len(poi_name) > 2:
                                rating_text = f"{poi_rating}星" if poi_rating not in (None, "") else "暂无评分"
                                message += f"    - {poi_name}（评分：{rating_text}）\n"
                    else:
                        message += f"  {category}：暂无符合条件的POI数据\n"
            else:
                message += "🎯 景点信息：暂无实时数据，可结合历史热门景点作为备选。\n"
            
            if "traffic" in real_time_data:
                traffic_info = real_time_data["traffic"]
                message += "🚦 交通信息：\n"
                for location, traffic in traffic_info.items():
                    if traffic and "status" in traffic:
                        message += f"  {location}：{traffic['status']}\n"
            
            if "crowd" in real_time_data:
                crowd_info = real_time_data["crowd"]
                message += "👥 人流信息：\n"
                for location, crowd in crowd_info.items():
                    if crowd and "description" in crowd:
                        message += f"  {location}：{crowd['description']}\n"
            
            if "analysis" in real_time_data:
                analysis_text = self._format_analysis_for_prompt(real_time_data["analysis"])
                message += "📊 综合推荐分析：\n"
                message += f"{analysis_text}\n"
        
        message += "\n请基于以上信息，为用户生成详细的旅游攻略。"
        
        return message
    
    def _extract_keywords(self, text: str) -> List[str]:
        """增强版关键词提取 - 更全面和精准"""
        keywords = []
        
        # 1. 提取地点关键词（包括变体）
        location_variants = {
            "华师大": ["华东师范大学", "华师大", "华东师大"],
            "迪士尼": ["迪士尼", "迪斯尼", "上海迪士尼", "迪士尼乐园"],
            "外滩": ["外滩", "黄浦江", "万国建筑"],
            "南京路": ["南京路", "南京东路", "南京西路", "步行街"],
            "豫园": ["豫园", "城隍庙", "老城厢"],
            "陆家嘴": ["陆家嘴", "东方明珠", "金融区", "上海中心"],
            "新天地": ["新天地", "石库门", "太平桥"],
            "田子坊": ["田子坊", "泰康路", "艺术街"],
            "徐家汇": ["徐家汇", "港汇", "太平洋百货"],
            "静安寺": ["静安寺", "久光", "嘉里中心"],
            "人民广场": ["人民广场", "人民公园", "上海博物馆"],
            "中山公园": ["中山公园", "龙之梦"],
            "五角场": ["五角场", "大学路", "合生汇"]
        }
        
        for main_location, variants in location_variants.items():
            if any(variant in text for variant in variants):
                keywords.append(main_location)
        
        # 2. 提取具体景点和建筑
        specific_places = [
            "东方明珠", "上海中心", "金茂大厦", "环球金融中心", "上海博物馆", 
            "上海科技馆", "上海海洋水族馆", "上海野生动物园", "朱家角", "七宝古镇",
            "思南公馆", "武康路", "多伦路", "1933老场坊", "M50创意园"
        ]
        for place in specific_places:
            if place in text:
                keywords.append(place)
        
        # 3. 提取活动类型关键词（更细致）
        activity_mapping = {
            "购物": ["逛街", "买", "商场", "百货", "奥特莱斯", "专卖店", "购物", "血拼"],
            "美食": ["吃", "餐厅", "小吃", "美食", "菜", "料理", "火锅", "烧烤", "本帮菜", "小笼包"],
            "文化": ["博物馆", "展览", "历史", "文化", "古迹", "艺术", "风情", "传统", "石库门"],
            "娱乐": ["游乐", "娱乐", "KTV", "电影", "酒吧", "夜生活", "迪士尼", "游戏"],
            "自然": ["公园", "花园", "湖", "江", "山", "海", "自然", "绿地", "植物园"],
            "商务": ["会议", "商务", "办公", "工作", "送", "接"],
            "亲子": ["孩子", "儿童", "亲子", "家庭", "带娃", "女儿", "儿子"],
            "休闲": ["散步", "休息", "放松", "慢", "悠闲", "清净", "安静"],
            "观光": ["观光", "游览", "参观", "看", "拍照", "打卡", "风景"]
        }
        
        for activity, activity_keywords in activity_mapping.items():
            if any(keyword in text for keyword in activity_keywords):
                keywords.append(activity)
        
        # 4. 提取人员关系关键词
        people_keywords = ["女朋友", "男朋友", "老婆", "老公", "妻子", "丈夫", "父母", "爸妈", 
                          "孩子", "女儿", "儿子", "家人", "朋友", "同事", "一家", "全家"]
        for people in people_keywords:
            if people in text:
                keywords.append(people)
        
        # 5. 提取时间关键词（更详细）
        time_patterns = ["明天", "后天", "今天", "周末", "工作日", "早上", "上午", "下午", "晚上", "夜里",
                        "第一天", "第二天", "第三天", "第四天", "第五天", "几天", "多天"]
        for time_word in time_patterns:
            if time_word in text:
                keywords.append(time_word)
        
        # 6. 提取偏好和限制关键词
        preference_keywords = {
            "避开人群": ["人少", "不想人多", "避开人群", "清净", "安静"],
            "不想远": ["不想远", "近一点", "附近", "不要太远"],
            "排队": ["排队", "等待", "人多", "拥挤"],
            "交通": ["开车", "自驾", "地铁", "公交", "打车", "走路", "骑车", "不开车"],
            "预算": ["便宜", "经济", "省钱", "贵", "高端", "奢华", "预算"],
            "天气": ["天气", "下雨", "晴天", "阴天", "温度", "冷", "热", "风", "雪"]
        }
        
        for pref_type, pref_words in preference_keywords.items():
            if any(word in text for word in pref_words):
                keywords.append(pref_type)
        
        # 7. 使用正则表达式提取数字+天
        import re
        day_matches = re.findall(r'(\d+)天', text)
        for day_match in day_matches:
            keywords.append(f"{day_match}天")
        
        # 8. 提取特殊需求关键词
        special_needs = ["浪漫", "温馨", "刺激", "新鲜", "特色", "地道", "网红", "小众", "经典"]
        for need in special_needs:
            if need in text:
                keywords.append(need)
        
        # 去重并返回
        return list(set(keywords))
    
    def _prioritize_keywords_for_inputtips(self, keywords: List[str], user_input: str) -> List[str]:
        """为输入提示API智能排序关键词优先级"""
        
        # 过滤无效关键词：纯数字、单个字符、常见停用词
        invalid_patterns = [
            r'^\d+$',  # 纯数字
            r'^[a-zA-Z]$',  # 单个字母
            r'^(的|了|是|在|有|和|与|或|但|而|也|都|就|还|更|最|很|非常|特别|非常|十分)$',  # 停用词
        ]
        import re
        
        filtered_keywords = []
        for keyword in keywords:
            # 跳过纯数字
            if keyword.isdigit():
                continue
            # 跳过单个字符
            if len(keyword.strip()) <= 1:
                continue
            # 跳过停用词
            is_invalid = False
            for pattern in invalid_patterns:
                if re.match(pattern, keyword.strip()):
                    is_invalid = True
                    break
            if not is_invalid:
                filtered_keywords.append(keyword)
        
        # 定义优先级权重
        priority_scores = {}
        
        for keyword in filtered_keywords:
            score = 0
            
            # 1. 地点类关键词优先级最高
            location_keywords = ["华师大", "迪士尼", "外滩", "南京路", "豫园", "陆家嘴", 
                               "新天地", "田子坊", "徐家汇", "静安寺", "人民广场"]
            if keyword in location_keywords:
                score += 100
            
            # 2. 具体景点建筑优先级很高
            specific_places = ["东方明珠", "上海中心", "金茂大厦", "环球金融中心", "上海博物馆", 
                              "上海科技馆", "朱家角", "七宝古镇", "思南公馆", "武康路"]
            if keyword in specific_places:
                score += 90
            
            # 3. 在用户输入中出现位置越靠前，优先级越高
            if keyword in user_input:
                position = user_input.find(keyword)
                score += max(50 - position // 10, 10)  # 位置越靠前分数越高
            
            # 4. 关键词长度适中的优先级较高（2-6个字符）
            if 2 <= len(keyword) <= 6:
                score += 20
            elif len(keyword) > 6:
                score -= 10  # 太长的关键词可能不是地点
            
            # 5. 排除一些通用词汇
            exclude_words = ["天气", "交通", "景点", "餐厅", "上海", "旅游", "攻略", "购物", 
                           "美食", "文化", "娱乐", "自然", "商务", "亲子", "休闲", "观光"]
            if keyword in exclude_words:
                score -= 50
            
            # 6. 数字+天 的关键词不适合输入提示
            if keyword.endswith("天") and any(c.isdigit() for c in keyword):
                score -= 30
            
            # 7. 人员关系词不适合输入提示
            people_words = ["女朋友", "老婆", "妻子", "父母", "女儿", "儿子", "家人", "朋友"]
            if keyword in people_words:
                score -= 40
            
            # 8. 偏好词汇不适合输入提示
            preference_words = ["避开人群", "不想远", "排队", "预算", "浪漫", "温馨"]
            if keyword in preference_words:
                score -= 35
            
            priority_scores[keyword] = score
        
        # 按分数排序，只返回分数大于0的关键词
        sorted_keywords = sorted(
            [(k, v) for k, v in priority_scores.items() if v > 0], 
            key=lambda x: x[1], 
            reverse=True
        )
        
        result = [k for k, v in sorted_keywords]
        logger.info(f"关键词优先级排序结果: {[(k, priority_scores[k]) for k in result[:10]]}")
        
        return result
    
    def _extract_travel_days(self, text: str) -> int:
        """提取旅行天数"""
        import re
        
        # 匹配数字+天/日
        day_patterns = [
            r'(\d+)\s*天',
            r'(\d+)\s*日',
            r'(\d+)\s*天游',
            r'(\d+)\s*日游'
        ]
        
        for pattern in day_patterns:
            match = re.search(pattern, text)
            if match:
                days = int(match.group(1))
                return max(1, min(days, 7))  # 限制在1-7天
        
        # 如果没有明确指定，根据关键词推断
        if "三天" in text or "3天" in text:
            return 3
        elif "两天" in text or "2天" in text:
            return 2
        elif "一天" in text or "1天" in text:
            return 1
        elif "四天" in text or "4天" in text:
            return 4
        elif "五天" in text or "5天" in text:
            return 5
        elif "未来" in text and "天" in text:
            return 3  # 默认3天
        
        return 1  # 默认1天
    
    def _analyze_user_intent(self, user_input: str) -> Tuple[List[str], List[str]]:
        """分析用户意图"""
        detected_locations = []
        activity_types = []
        
        # 检测地点
        for location, attractions in self.location_keywords.items():
            if location in user_input:
                detected_locations.append(location)
        
        # 检测活动类型
        for activity, keywords in self.activity_keywords.items():
            if any(keyword in user_input for keyword in keywords):
                activity_types.append(activity)
        
        return detected_locations, activity_types
    
    def _extract_locations_from_input(self, user_input: str) -> List[str]:
        """从用户输入中提取地点信息"""
        locations = []
        
        # 上海地区关键词
        shanghai_areas = [
            "外滩", "人民广场", "南京路", "豫园", "陆家嘴", "东方明珠", 
            "上海迪士尼", "上海博物馆", "上海科技馆", "田子坊", "新天地",
            "金沙江路", "中山公园", "静安寺", "徐家汇", "五角场", "虹桥",
            "浦东", "浦西", "黄浦区", "静安区", "徐汇区", "长宁区", "普陀区",
            "华东师范大学", "华东师大", "华师大", "徐汇", "普陀"
        ]
        
        for area in shanghai_areas:
            if area in user_input:
                locations.append(area)
        
        # 去重并过滤
        locations = list(set(locations))
        return locations
    
    def _is_valid_location(self, location_name: str, keyword: str) -> bool:
        """判断是否是有效的地点名称"""
        if not location_name or len(location_name.strip()) < 2:
            return False
        
        # 过滤掉明显不是地点的结果
        invalid_patterns = ['%', '会议', '中心', '购物', '艺术中心']
        location_lower = location_name.lower()
        
        # 如果关键词是数字，直接拒绝
        if keyword.isdigit():
            return False
        
        # 如果地点名称包含关键词，认为是相关的
        if keyword in location_name:
            return True
        
        # 如果地点名称包含无效模式，拒绝
        for pattern in invalid_patterns:
            if pattern in location_name and keyword not in location_name:
                return False
        
        return True
    
    def _extract_route_from_input(self, user_input: str) -> Optional[Dict[str, str]]:
        """从用户输入中提取路线信息"""
        # 简单的路线提取逻辑
        if "从" in user_input and "到" in user_input:
            parts = user_input.split("从")[1].split("到")
            if len(parts) >= 2:
                start = parts[0].strip()
                end = parts[1].split()[0].strip()  # 取第一个词作为终点
                return {"start": start, "end": end}
        
        return None
    
    def _infer_route_from_input(self, user_input: str) -> Optional[Dict[str, str]]:
        """从用户输入中推断路线信息"""
        # 特殊处理：华东师范大学到徐汇区
        if "华东师范大学" in user_input and "徐汇区" in user_input:
            return {"start": "华东师范大学", "end": "徐汇区"}
        
        # 提取地点信息
        locations = self._extract_locations_from_input(user_input)
        
        # 如果找到多个地点，尝试推断起点和终点
        if len(locations) >= 2:
            # 根据用户输入中的关键词推断
            if "出发" in user_input:
                # 找到"出发"前面的地点作为起点
                for i, location in enumerate(locations):
                    if location in user_input[:user_input.find("出发")]:
                        start = location
                        # 其他地点作为终点
                        end = locations[(i + 1) % len(locations)]
                        return {"start": start, "end": end}
            
            # 如果没有"出发"关键词，使用第一个地点作为起点，最后一个作为终点
            return {"start": locations[0], "end": locations[-1]}
        
        return None
    

    
    # MCP服务方法（从smart_travel_agent.py移植）
    def _rate_limit_wait(self, api_name: str):
        """API限流控制 - 确保不超过QPS限制"""
        with self._api_lock:
            current_time = time.time()
            if api_name in self._last_api_call:
                elapsed = current_time - self._last_api_call[api_name]
                if elapsed < self._min_interval:
                    wait_time = self._min_interval - elapsed
                    logger.debug(f"限流等待 {wait_time:.2f}秒 for {api_name}")
                    time.sleep(wait_time)
            self._last_api_call[api_name] = time.time()
    
    def _make_request(self, url: str, params: Dict[str, Any], api_name: str = "default") -> Dict[str, Any]:
        """发送HTTP请求（带限流控制）"""
        try:
            # 限流控制
            self._rate_limit_wait(api_name)
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"API请求失败: {url}, 错误: {e}")
            return {}
    
    def get_weather(self, city: str, date: str = None) -> List[WeatherInfo]:
        """获取天气信息 - 使用MCP服务"""
        return self.mcp_client.call_service(MCPServiceType.WEATHER, city=city, date=date) or []
    
    def get_navigation_routes(self, origin: str, destination: str, 
                            transport_mode: str = "driving") -> List[RouteInfo]:
        """获取导航路线 - 使用MCP服务"""
        return self.mcp_client.call_service(
            MCPServiceType.NAVIGATION,
            origin=origin,
            destination=destination,
            transport_mode=transport_mode
        ) or []
    
    def get_traffic_status(self, area: str) -> Dict[str, Any]:
        """获取路况信息 - 使用MCP服务"""
        result = self.mcp_client.call_service(MCPServiceType.TRAFFIC, area=area)
        if result:
            return result
        # 返回默认数据
        return {
            "status": "正常",
            "description": "路况良好",
            "evaluation": {"level": "1", "status": "畅通"},
            "timestamp": datetime.now().isoformat()
        }
            
    def search_poi(self, keyword: str, city: str, category: str = None) -> List[POIInfo]:
        """搜索POI信息 - 使用MCP服务"""
        return self.mcp_client.call_service(
            MCPServiceType.POI,
            keyword=keyword,
            city=city,
            category=category
        ) or []
    
    def _filter_shanghai_only(self, pois: List[POIInfo]) -> List[POIInfo]:
        """过滤掉非上海地区的POI，确保只返回上海景点"""
        filtered = []
        
        # 非上海城市关键词（排除上海的街道名）
        non_shanghai_cities = [
            "北京", "广州", "深圳", "杭州", "南京", "苏州", "成都", "重庆",
            "西安", "武汉", "天津", "长沙", "郑州", "济南", "青岛", "大连",
            "厦门", "福州", "合肥", "南昌", "石家庄", "太原", "哈尔滨", "长春",
            "沈阳", "昆明", "贵阳", "南宁", "海口", "乌鲁木齐", "拉萨", "银川",
            "西宁", "兰州", "呼和浩特"
        ]
        
        # 上海的街道名（这些应该保留）
        shanghai_streets = [
            "北京东路", "北京西路", "南京东路", "南京西路", "淮海东路", "淮海西路",
            "中山北路", "中山南路", "中山中路", "中山东路", "中山南路", "中山北路",
            "延安东路", "延安西路", "延安中路", "四川北路", "四川南路", "四川中路"
        ]
        
        for poi in pois:
            name = poi.name or ""
            address = poi.address or ""
            full_text = f"{name} {address}".lower()
            
            # 检查是否包含非上海城市关键词
            is_non_shanghai = False
            for city in non_shanghai_cities:
                if city in full_text:
                    # 检查是否是上海的街道名
                    is_shanghai_street = any(street in name or street in address for street in shanghai_streets)
                    if not is_shanghai_street:
                        is_non_shanghai = True
                        logger.warning(f"过滤非上海POI: {name} (地址: {address}) - 包含城市: {city}")
                        break
            
            # 检查地址中是否明确包含非上海城市
            if not is_non_shanghai:
                # 检查districts格式（如"北京·北京·朝阳区"）
                if "·" in address:
                    parts = address.split("·")
                    if len(parts) >= 2 and parts[0] not in ["上海", "Shanghai", "shanghai"]:
                        is_non_shanghai = True
                        logger.warning(f"过滤非上海POI: {name} (地址: {address}) - districts格式显示非上海")
            
            if not is_non_shanghai:
                filtered.append(poi)
        
        if len(filtered) < len(pois):
            logger.info(f"POI过滤: 原始{len(pois)}个，过滤后{len(filtered)}个（已过滤{len(pois) - len(filtered)}个非上海POI）")
        
        return filtered
    
    def get_inputtips(self, keywords: str, city: str = "上海", 
                      poi_type: str = None, location: str = None, 
                      citylimit: bool = False, datatype: str = "all") -> List[Dict[str, Any]]:
        """获取输入提示 - 根据关键词返回建议列表
        
        Args:
            keywords: 查询关键词
            city: 搜索城市（默认：上海）
            poi_type: POI分类代码，多个用"|"分隔
            location: 坐标，格式"经度,纬度"，可优先返回此位置附近的结果
            citylimit: 是否仅返回指定城市数据（True/False）
            datatype: 返回数据类型（all/poi/bus/busline）
            
        Returns:
            建议列表
        """
        logger.info(f"调用输入提示API: {keywords} in {city}")
        
        try:
            params = {
                "key": get_api_key("AMAP_PROMPT"),
                "keywords": keywords,
                "city": city,
                "citylimit": "true" if citylimit else "false",
                "datatype": datatype
            }
            
            # 可选参数
            if poi_type:
                params["type"] = poi_type
            if location:
                params["location"] = location
            
            result = self._make_request(AMAP_CONFIG["inputtips_url"], params, "inputtips")
            
            if result.get("status") == "1":
                tips = []
                for tip_data in result.get("tips", []):
                    tip_info = {
                        "id": tip_data.get("id", ""),
                        "name": tip_data.get("name", ""),
                        "district": tip_data.get("district", ""),
                        "adcode": tip_data.get("adcode", ""),
                        "location": tip_data.get("location", ""),
                        "address": tip_data.get("address", ""),
                        "typecode": tip_data.get("typecode", "")
                    }
                    tips.append(tip_info)
                
                logger.info(f"输入提示API调用成功: {keywords} - {len(tips)}个建议")
                return tips
            else:
                logger.error(f"输入提示API调用失败: {result.get('info', '未知错误')}")
                
        except Exception as e:
            logger.error(f"获取输入提示失败: {e}")
        
        return []
    
    def _geocode(self, address: str) -> Optional[str]:
        """地理编码"""
        try:
            params = {
                "key": get_api_key("AMAP_POI"),
                "address": address
            }
            
            result = self._make_request(AMAP_CONFIG["geocode_url"], params, "geocode")
            
            if result.get("status") == "1":
                geocodes = result.get("geocodes", [])
                if geocodes:
                    return geocodes[0].get("location", "")
        except Exception as e:
            logger.error(f"地理编码失败: {e}")
        
        return None
    
    def _get_city_code(self, city_name: str) -> str:
        """获取城市代码"""
        city_codes = {
            "上海": "310000", "北京": "110000", "广州": "440100",
            "深圳": "440300", "杭州": "330100", "南京": "320100",
            "苏州": "320500", "成都": "510100", "重庆": "500000"
        }
        return city_codes.get(city_name, "310000")
    
    def _get_area_coordinates(self, area: str) -> Optional[str]:
        """获取区域坐标范围"""
        area_coords = {
            "外滩": "121.4805,31.2304,121.5005,31.2504",
            "陆家嘴": "121.4978,31.2297,121.5178,31.2497",
            "人民广场": "121.4637,31.2216,121.4837,31.2416"
        }
        return area_coords.get(area, None)
    
    def _format_transit_route(self, route: Dict[str, Any]) -> str:
        """格式化公交路线描述"""
        segments = route.get("segments", [])
        description = []
        
        for segment in segments:
            bus_info = segment.get("bus", {})
            if bus_info:
                bus_name = bus_info.get("busname", "")
                bus_stops = bus_info.get("buslines", [{}])[0].get("departure_stop", "")
                arrival_stops = bus_info.get("buslines", [{}])[0].get("arrival_stop", "")
                description.append(f"{bus_name}: {bus_stops} → {arrival_stops}")
        
        return " → ".join(description)
    
    def _format_driving_route(self, route: Dict[str, Any]) -> str:
        """格式化驾车路线描述"""
        steps = route.get("steps", [])
        description = []
        
        for step in steps[:3]:
            instruction = step.get("instruction", "")
            if instruction:
                description.append(instruction.split("，")[0])
        
        return " → ".join(description)

def main():
    """测试增强版Agent"""
    agent = EnhancedTravelAgent()
    
    print("🤖 增强版智能旅行对话Agent (豆包版)")
    print("=" * 60)
    print("输入 'quit' 退出对话")
    print("=" * 60)
    
    while True:
        try:
            user_input = input("\n👤 您: ").strip()
            
            if user_input.lower() in ['quit', 'exit', '退出']:
                print("👋 再见！")
                break
            
            if not user_input:
                continue
            
            # 处理用户请求
            response = agent.process_user_request(user_input, "test_user")
            
            print(f"\n🤖 Agent: {response}")
            
        except KeyboardInterrupt:
            print("\n👋 再见！")
            break
        except Exception as e:
            print(f"\n❌ 错误: {e}")

if __name__ == "__main__":
    main()
