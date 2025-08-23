#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MCP+RAG集成系统
将实时MCP服务数据与RAG知识库检索相结合
为上海旅游AI提供全面的智能信息服务
"""

import os
import json
import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
import logging

from mcp_services import MCPServiceManager, WeatherMCPService, CrowdMCPService, TrafficMCPService
from rag_retrieval import HybridRAGRetriever, RetrievalResult, format_retrieval_results

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MCPRAGIntegrator:
    """MCP+RAG集成器"""
    
    def __init__(self, data_dir: str = "./data"):
        """初始化集成器"""
        self.data_dir = data_dir
        
        # 初始化MCP服务管理器
        self.mcp_manager = MCPServiceManager()
        
        # 初始化RAG检索器
        self.rag_retriever = HybridRAGRetriever(data_dir)
        
        # 服务状态
        self.mcp_available = True
        self.rag_available = False
        
        # 查询分类器配置
        self.query_patterns = {
            'realtime': {
                'keywords': ['现在', '实时', '当前', '今天', '目前', '最新', '刚才'],
                'services': ['weather', 'crowd', 'traffic']
            },
            'historical': {
                'keywords': ['历史', '以前', '过去', '曾经', '之前'],
                'services': ['rag']
            },
            'planning': {
                'keywords': ['规划', '安排', '计划', '路线', '行程', '建议', '推荐'],
                'services': ['rag', 'mcp']
            },
            'detailed': {
                'keywords': ['详细', '介绍', '信息', '攻略', '说明', '特色', '亮点'],
                'services': ['rag']
            },
            'practical': {
                'keywords': ['门票', '开放时间', '地址', '电话', '交通', '价格', '费用'],
                'services': ['rag', 'mcp']
            }
        }
        
    def initialize(self) -> bool:
        """初始化系统"""
        logger.info("初始化MCP+RAG集成系统...")
        
        try:
            # 初始化RAG检索器
            self.rag_available = self.rag_retriever.load_corpus()
            
            # 检查MCP服务
            test_result = self.mcp_manager.get_integrated_info("测试查询")
            self.mcp_available = len(test_result) > 0
            
            logger.info(f"系统初始化完成 - RAG: {'可用' if self.rag_available else '不可用'}, MCP: {'可用' if self.mcp_available else '不可用'}")
            
            return self.rag_available or self.mcp_available
            
        except Exception as e:
            logger.error(f"系统初始化失败: {e}")
            return False
    
    def classify_query(self, query: str) -> Dict[str, Any]:
        """分析查询类型和需求"""
        classification = {
            'query_type': 'general',
            'needs_realtime': False,
            'needs_detailed': False,
            'needs_planning': False,
            'location': None,
            'services_needed': [],
            'confidence': 0.0
        }
        
        query_lower = query.lower()
        scores = {}
        
        # 检查各种查询模式
        for pattern_name, pattern_config in self.query_patterns.items():
            score = 0
            for keyword in pattern_config['keywords']:
                if keyword in query_lower:
                    score += 1
            
            if score > 0:
                scores[pattern_name] = score / len(pattern_config['keywords'])
        
        # 确定主要查询类型
        if scores:
            best_type = max(scores.keys(), key=lambda k: scores[k])
            classification['query_type'] = best_type
            classification['confidence'] = scores[best_type]
            classification['services_needed'] = self.query_patterns[best_type]['services'].copy()
        
        # 特殊判断
        classification['needs_realtime'] = any(kw in query_lower for kw in ['现在', '实时', '当前', '今天', '目前'])
        classification['needs_detailed'] = any(kw in query_lower for kw in ['详细', '介绍', '攻略', '特色'])
        classification['needs_planning'] = any(kw in query_lower for kw in ['规划', '推荐', '建议', '路线'])
        
        # 提取地点信息
        classification['location'] = self._extract_location(query)
        
        return classification
    
    def _extract_location(self, query: str) -> Optional[str]:
        """提取查询中的地点信息"""
        # 上海景点列表
        locations = [
            '外滩', '东方明珠', '豫园', '城隍庙', '南京路', '新天地', '田子坊',
            '朱家角', '七宝古镇', '上海博物馆', '上海科技馆', '迪士尼', '野生动物园',
            '植物园', '中山公园', '人民广场', '陆家嘴', '静安寺', '徐家汇',
            '虹桥', '浦东机场', '虹桥机场', '黄浦江', '苏州河', '世博园',
            '上海大剧院', '音乐厅', '美术馆', '自然博物馆', '海洋馆'
        ]
        
        for location in locations:
            if location in query:
                return location
        
        return None
    
    def get_integrated_response(self, query: str) -> Dict[str, Any]:
        """获取集成响应"""
        response = {
            'query': query,
            'timestamp': datetime.now().isoformat(),
            'classification': {},
            'mcp_data': {},
            'rag_results': [],
            'integrated_content': '',
            'confidence': 0.0,
            'sources': []
        }
        
        try:
            # 1. 分析查询
            classification = self.classify_query(query)
            response['classification'] = classification
            
            # 2. 获取实时数据
            if (classification['needs_realtime'] or 'mcp' in classification['services_needed']) and self.mcp_available:
                mcp_data = self.mcp_manager.get_integrated_info(query)
                response['mcp_data'] = mcp_data
                if mcp_data:
                    response['sources'].append('实时数据')
            
            # 3. 获取知识库信息
            if ('rag' in classification['services_needed'] or classification['needs_detailed']) and self.rag_available:
                rag_results = self._get_rag_information(query, classification)
                response['rag_results'] = rag_results
                if rag_results:
                    response['sources'].append('知识库')
            
            # 4. 集成信息
            integrated_content = self._integrate_information(query, classification, response['mcp_data'], response['rag_results'])
            response['integrated_content'] = integrated_content
            
            # 5. 计算置信度
            response['confidence'] = self._calculate_confidence(response)
            
        except Exception as e:
            logger.error(f"获取集成响应失败: {e}")
            response['integrated_content'] = f"抱歉，处理您的查询时出现错误：{str(e)}"
        
        return response
    
    def _get_rag_information(self, query: str, classification: Dict) -> List[Dict]:
        """获取RAG检索信息"""
        rag_results = []
        
        try:
            # 根据查询类型调整检索策略
            if classification['query_type'] == 'detailed':
                # 详细信息查询：优先景点信息
                attraction_results = self.rag_retriever.search_attractions(query, top_k=2)
                guide_results = self.rag_retriever.search_guides(query, top_k=2)
                rag_results.extend(self._format_rag_results(attraction_results + guide_results))
                
            elif classification['query_type'] == 'planning':
                # 规划类查询：优先攻略信息
                guide_results = self.rag_retriever.search_guides(query, top_k=3)
                attraction_results = self.rag_retriever.search_attractions(query, top_k=1)
                rag_results.extend(self._format_rag_results(guide_results + attraction_results))
                
            elif classification['query_type'] == 'practical':
                # 实用信息查询：景点详细信息
                attraction_results = self.rag_retriever.search_attractions(query, top_k=2)
                review_results = self.rag_retriever.search_reviews(query, top_k=1)
                rag_results.extend(self._format_rag_results(attraction_results + review_results))
                
            else:
                # 通用查询：混合检索
                mixed_results = self.rag_retriever.search(query, top_k=3)
                rag_results.extend(self._format_rag_results(mixed_results))
        
        except Exception as e:
            logger.error(f"RAG检索失败: {e}")
        
        return rag_results
    
    def _format_rag_results(self, results: List[RetrievalResult]) -> List[Dict]:
        """格式化RAG检索结果"""
        formatted_results = []
        
        for result in results:
            formatted_result = {
                'title': result.title,
                'content': result.content[:500] + "..." if len(result.content) > 500 else result.content,
                'type': result.doc_type,
                'score': result.score,
                'metadata': result.metadata
            }
            formatted_results.append(formatted_result)
        
        return formatted_results
    
    def _integrate_information(self, query: str, classification: Dict, mcp_data: Dict, rag_results: List[Dict]) -> str:
        """集成MCP和RAG信息"""
        parts = []
        location = classification.get('location', '上海')
        
        # 添加查询确认
        parts.append(f"📍 关于{location}的信息：")
        
        # 1. 实时信息部分
        if mcp_data:
            realtime_info = self.mcp_manager.format_response(mcp_data, query)
            if realtime_info:
                parts.append("🔴 **实时信息**")
                parts.append(realtime_info)
        
        # 2. 详细知识部分
        if rag_results:
            parts.append("📚 **详细资料**")
            
            for i, result in enumerate(rag_results[:3], 1):
                content_preview = result['content'][:200] + "..." if len(result['content']) > 200 else result['content']
                
                result_text = f"**{i}. {result['title']}**"
                if result['type'] == 'attraction':
                    result_text += " 🏛️"
                elif result['type'] == 'guide':
                    result_text += " 📖"
                elif result['type'] == 'reviews':
                    result_text += " 💬"
                
                result_text += f"\n{content_preview}"
                parts.append(result_text)
        
        # 3. 综合建议
        if mcp_data or rag_results:
            suggestions = self._generate_suggestions(query, classification, mcp_data, rag_results)
            if suggestions:
                parts.append("💡 **智能建议**")
                parts.append(suggestions)
        
        # 4. 如果没有足够信息
        if not mcp_data and not rag_results:
            parts.append("😅 抱歉，暂时没有找到相关信息。")
            parts.append("您可以尝试：")
            parts.append("• 换一个表达方式")
            parts.append("• 指定具体的景点名称")
            parts.append("• 询问其他上海旅游信息")
        
        return "\n\n".join(parts)
    
    def _generate_suggestions(self, query: str, classification: Dict, mcp_data: Dict, rag_results: List[Dict]) -> str:
        """生成智能建议"""
        suggestions = []
        
        try:
            # 基于实时数据的建议
            if mcp_data:
                if 'weather' in mcp_data:
                    weather = mcp_data['weather']
                    if weather.get('condition') == '雨':
                        suggestions.append("• 今天有雨，建议选择室内景点或准备雨具")
                    elif weather.get('temperature', 0) > 30:
                        suggestions.append("• 天气较热，建议避开中午时段，多补充水分")
                
                if 'crowd' in mcp_data:
                    crowd = mcp_data['crowd']
                    if crowd.get('crowd_level', 0) > 70:
                        suggestions.append("• 当前人流较多，建议选择其他时间或替代景点")
                
                if 'traffic' in mcp_data:
                    traffic = mcp_data['traffic']
                    if '拥堵' in traffic.get('congestion_level', ''):
                        suggestions.append("• 交通拥堵，建议使用公共交通工具")
            
            # 基于知识库的建议
            if rag_results:
                # 提取开放时间信息
                for result in rag_results:
                    content = result['content'].lower()
                    if '开放时间' in content or '营业时间' in content:
                        suggestions.append("• 请注意景点的开放时间，建议提前确认")
                        break
                
                # 提取门票信息
                for result in rag_results:
                    content = result['content'].lower()
                    if '门票' in content or '票价' in content:
                        suggestions.append("• 建议提前在线购票，可能有优惠且避免排队")
                        break
            
            # 基于查询类型的建议
            if classification['query_type'] == 'planning':
                suggestions.append("• 建议合理安排时间，预留足够的游览和交通时间")
            
            if classification['needs_realtime']:
                suggestions.append("• 出发前可以再次查询最新的实时信息")
        
        except Exception as e:
            logger.warning(f"生成建议时出错: {e}")
        
        return '\n'.join(suggestions) if suggestions else ""
    
    def _calculate_confidence(self, response: Dict) -> float:
        """计算响应置信度"""
        confidence = 0.0
        
        # 基础分数
        if response['mcp_data']:
            confidence += 0.3
        
        if response['rag_results']:
            confidence += 0.4
        
        # RAG结果质量加分
        if response['rag_results']:
            avg_score = sum(r['score'] for r in response['rag_results']) / len(response['rag_results'])
            confidence += min(avg_score * 0.3, 0.3)
        
        # 分类置信度加分
        classification_conf = response['classification'].get('confidence', 0)
        confidence += classification_conf * 0.2
        
        return min(confidence, 1.0)
    
    def get_system_status(self) -> Dict:
        """获取系统状态"""
        status = {
            'mcp_available': self.mcp_available,
            'rag_available': self.rag_available,
            'initialization_time': datetime.now().isoformat(),
        }
        
        # MCP服务状态
        if self.mcp_available:
            status['mcp_services'] = {
                'weather': True,
                'crowd': True,
                'traffic': True
            }
        
        # RAG检索器状态
        if self.rag_available:
            rag_stats = self.rag_retriever.get_stats()
            status['rag_stats'] = rag_stats
        
        return status
    
    def batch_query(self, queries: List[str]) -> List[Dict]:
        """批量查询处理"""
        results = []
        
        for query in queries:
            try:
                result = self.get_integrated_response(query)
                results.append(result)
            except Exception as e:
                error_result = {
                    'query': query,
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                }
                results.append(error_result)
        
        return results

class EnhancedTourismAssistant:
    """增强版旅游助手"""
    
    def __init__(self, data_dir: str = "./data", api_key: str = None):
        """初始化增强版助手"""
        self.data_dir = data_dir
        self.api_key = api_key
        
        # 初始化MCP+RAG集成器
        self.integrator = MCPRAGIntegrator(data_dir)
        self.integration_available = False
        
        # 保持原有API调用能力
        self.api_url = "https://ark.cn-beijing.volces.com/api/v3/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {api_key or os.getenv('DOUBAO_API_KEY')}",
            "Content-Type": "application/json"
        }
        
    def initialize(self) -> bool:
        """初始化系统"""
        self.integration_available = self.integrator.initialize()
        return self.integration_available
    
    def generate_response(self, query: str, use_integration: bool = True) -> str:
        """生成智能回复"""
        try:
            if use_integration and self.integration_available:
                # 使用MCP+RAG集成响应
                integrated_response = self.integrator.get_integrated_response(query)
                
                if integrated_response['confidence'] > 0.3:
                    return integrated_response['integrated_content']
                else:
                    # 置信度不够，尝试AI增强
                    return self._enhance_with_ai(query, integrated_response)
            else:
                # 降级到传统模式
                return self._traditional_response(query)
                
        except Exception as e:
            logger.error(f"生成回复失败: {e}")
            return f"抱歉，处理您的问题时出现了错误。请稍后再试。"
    
    def _enhance_with_ai(self, query: str, integrated_response: Dict) -> str:
        """用AI增强集成响应"""
        # 构建增强提示词
        context_parts = []
        
        if integrated_response['mcp_data']:
            context_parts.append("实时数据：" + json.dumps(integrated_response['mcp_data'], ensure_ascii=False))
        
        if integrated_response['rag_results']:
            rag_content = "\n".join([f"- {r['title']}: {r['content'][:200]}" for r in integrated_response['rag_results'][:3]])
            context_parts.append(f"知识库信息：\n{rag_content}")
        
        context = "\n\n".join(context_parts) if context_parts else "暂无相关信息"
        
        prompt = f"""基于以下信息回答用户问题：

{context}

用户问题：{query}

请提供准确、有用的回答，如果信息不够充分，请诚实说明。"""
        
        return self._call_ai_api(prompt)
    
    def _traditional_response(self, query: str) -> str:
        """传统响应方式"""
        prompt = f"""你是上海旅游专家，请回答关于上海旅游的问题：{query}

请提供实用、准确的建议。"""
        
        return self._call_ai_api(prompt)
    
    def _call_ai_api(self, prompt: str) -> str:
        """调用AI API"""
        try:
            import requests
            
            payload = {
                "model": "doubao-1-5-pro-32k-250115",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.7,
                "max_tokens": 1500
            }
            
            response = requests.post(
                self.api_url,
                headers=self.headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()['choices'][0]['message']['content']
            else:
                return f"AI服务暂时不可用，请稍后再试。"
                
        except Exception as e:
            logger.error(f"AI API调用失败: {e}")
            return "AI服务暂时不可用，建议您查阅相关旅游指南或联系客服。"
    
    def get_comprehensive_info(self, attraction: str) -> Dict:
        """获取景点综合信息"""
        query = f"{attraction}详细信息"
        
        # 获取集成响应
        response = self.integrator.get_integrated_response(query)
        
        # 格式化为结构化信息
        comprehensive_info = {
            'attraction': attraction,
            'realtime_data': response.get('mcp_data', {}),
            'detailed_info': response.get('rag_results', []),
            'recommendations': self._extract_recommendations(response),
            'last_updated': datetime.now().isoformat()
        }
        
        return comprehensive_info
    
    def _extract_recommendations(self, response: Dict) -> List[str]:
        """从响应中提取建议"""
        content = response.get('integrated_content', '')
        
        # 简单提取建议段落
        recommendations = []
        lines = content.split('\n')
        
        in_suggestions = False
        for line in lines:
            if '建议' in line or '💡' in line:
                in_suggestions = True
                continue
            
            if in_suggestions and line.strip():
                if line.startswith('•') or line.startswith('-'):
                    recommendations.append(line.strip())
                elif line.startswith('#') or line.startswith('**'):
                    break
        
        return recommendations

# 工具函数
def run_integration_test():
    """运行集成测试"""
    print("🧪 MCP+RAG集成系统测试")
    print("=" * 50)
    
    # 初始化系统
    assistant = EnhancedTourismAssistant()
    if not assistant.initialize():
        print("❌ 系统初始化失败")
        return
    
    print("✅ 系统初始化成功")
    
    # 测试查询
    test_queries = [
        "外滩现在天气怎么样？",
        "东方明珠的详细介绍",
        "上海博物馆开放时间",
        "迪士尼乐园游玩攻略",
        "南京路现在人多吗？",
        "帮我规划上海一日游"
    ]
    
    for query in test_queries:
        print(f"\n🔍 测试查询：{query}")
        print("-" * 30)
        
        response = assistant.generate_response(query)
        print(response)
        print("=" * 50)
    
    # 系统状态
    status = assistant.integrator.get_system_status()
    print(f"\n📊 系统状态：")
    print(json.dumps(status, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    run_integration_test()

