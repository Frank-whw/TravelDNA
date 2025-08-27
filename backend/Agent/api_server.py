#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
上海旅游AI助手 - Flask API服务器
将AI助手功能包装为REST API，供前端调用
"""

import os
import json
import traceback
from datetime import datetime
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from functools import wraps
import logging

# 导入核心模块
from model import TourismAssistant
from config import Config
from data_loader import get_data_statistics
from mcp_services import MCPServiceManager

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 创建Flask应用
app = Flask(__name__)
CORS(app)  # 启用跨域支持

# 全局配置
app.config['JSON_AS_ASCII'] = False  # 支持中文JSON响应
app.config['SECRET_KEY'] = 'shanghai_tourism_ai_2024'

# 全局变量
tourism_assistant = None
mcp_manager = None
assistant_initialized = False

# API限流配置
API_RATE_LIMIT = {
    'requests_per_minute': 60,
    'requests_per_hour': 1000
}

# 用户会话管理
user_sessions = {}

def init_services():
    """初始化服务"""
    global tourism_assistant, mcp_manager, assistant_initialized
    
    try:
        logger.info("🚀 正在初始化上海旅游AI服务...")
        
        # 初始化AI助手
        tourism_assistant = TourismAssistant(use_enhanced=True)
        assistant_initialized = tourism_assistant.initialize_enhanced_system()
        
        # 初始化MCP服务管理器（包含交通MCP服务）
        mcp_manager = MCPServiceManager()
        
        logger.info(f"✅ 服务初始化完成 - AI助手: {'可用' if assistant_initialized else '不可用'}")
        logger.info(f"🚦 MCP服务管理器: 已初始化（包含天气、人流、交通MCP）")
        return True
        
    except Exception as e:
        logger.error(f"❌ 服务初始化失败: {e}")
        return False

def api_response(success=True, data=None, message="", error_code=None):
    """统一API响应格式"""
    response = {
        "success": success,
        "timestamp": datetime.now().isoformat(),
        "message": message,
        "data": data
    }
    
    if error_code:
        response["error_code"] = error_code
    
    return jsonify(response)

def error_handler(f):
    """API错误处理装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            logger.error(f"API错误 {request.endpoint}: {str(e)}\n{traceback.format_exc()}")
            return api_response(
                success=False,
                message=f"服务器内部错误: {str(e)}",
                error_code="INTERNAL_ERROR"
            ), 500
    return decorated_function

def validate_request(required_fields=None):
    """请求参数验证装饰器"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # 检查Content-Type
            if request.method == 'POST' and not request.is_json:
                return api_response(
                    success=False,
                    message="请求必须是JSON格式",
                    error_code="INVALID_CONTENT_TYPE"
                ), 400
            
            # 检查必需字段
            if required_fields:
                data = request.get_json() if request.is_json else request.args
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    return api_response(
                        success=False,
                        message=f"缺少必需参数: {', '.join(missing_fields)}",
                        error_code="MISSING_PARAMETERS"
                    ), 400
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# =================== API路由定义 ===================

@app.route('/', methods=['GET'])
def health_check():
    """健康检查端点"""
    return api_response(
        data={
            "service": "上海旅游AI助手API",
            "version": "1.0.0",
            "status": "运行中",
            "ai_available": assistant_initialized,
            "timestamp": datetime.now().isoformat()
        },
        message="服务运行正常"
    )

@app.route('/api/status', methods=['GET'])
@error_handler
def get_service_status():
    """获取服务状态"""
    if not tourism_assistant:
        return api_response(
            success=False,
            message="服务未初始化",
            error_code="SERVICE_NOT_INITIALIZED"
        ), 503
    
    status = tourism_assistant.get_service_status()
    data_stats = get_data_statistics()
    
    return api_response(
        data={
            "service_status": status,
            "data_statistics": data_stats,
                            "api_info": {
                "rate_limit": API_RATE_LIMIT,
                "supported_methods": ["chat", "realtime", "attractions", "planning", "traffic"]
            }
        },
        message="状态获取成功"
    )

@app.route('/api/chat', methods=['POST'])
@error_handler
@validate_request(['message'])
def chat():
    """智能对话接口"""
    if not tourism_assistant:
        return api_response(
            success=False,
            message="AI助手服务不可用",
            error_code="SERVICE_UNAVAILABLE"
        ), 503
    
    data = request.get_json()
    message = data.get('message', '').strip()
    user_id = data.get('user_id', 'anonymous')
    conversation_id = data.get('conversation_id')
    
    # 验证消息长度
    if len(message) > Config.MAX_QUERY_LENGTH:
        return api_response(
            success=False,
            message=f"消息长度不能超过{Config.MAX_QUERY_LENGTH}字符",
            error_code="MESSAGE_TOO_LONG"
        ), 400
    
    # 检查敏感词
    if any(blocked in message.lower() for blocked in Config.BLOCKED_KEYWORDS):
        return api_response(
            success=False,
            message="消息包含不当内容",
            error_code="BLOCKED_CONTENT"
        ), 400
    
    try:
        # 生成回复
        start_time = datetime.now()
        response_text = tourism_assistant.generate_response(message)
        end_time = datetime.now()
        
        response_time = (end_time - start_time).total_seconds()
        
        # 构建响应数据
        response_data = {
            "response": response_text,
            "conversation_id": conversation_id or f"{user_id}_{int(datetime.now().timestamp())}",
            "response_time": round(response_time, 2),
            "timestamp": end_time.isoformat(),
            "user_query": message,
            "mode": "enhanced" if assistant_initialized else "traditional"
        }
        
        # 记录对话历史（可选）
        if user_id not in user_sessions:
            user_sessions[user_id] = []
        
        user_sessions[user_id].append({
            "query": message,
            "response": response_text,
            "timestamp": end_time.isoformat()
        })
        
        # 保持会话历史在合理范围内
        if len(user_sessions[user_id]) > 10:
            user_sessions[user_id] = user_sessions[user_id][-10:]
        
        return api_response(
            data=response_data,
            message="对话成功"
        )
        
    except Exception as e:
        logger.error(f"对话处理失败: {e}")
        return api_response(
            success=False,
            message="AI服务暂时不可用，请稍后再试",
            error_code="AI_SERVICE_ERROR"
        ), 500

@app.route('/api/weather/<location>', methods=['GET'])
@error_handler
def get_weather_info(location):
    """获取指定地点的天气信息"""
    if not mcp_manager:
        return api_response(
            success=False,
            message="天气服务不可用",
            error_code="WEATHER_SERVICE_UNAVAILABLE"
        ), 503
    
    city = request.args.get('city', '上海')
    forecast = request.args.get('forecast', 'false').lower() == 'true'
    
    try:
        if forecast:
            # 获取天气预报
            weather_data = mcp_manager.weather_service.get_weather_forecast(city)
        else:
            # 获取当前天气
            weather_data = mcp_manager.weather_service.get_weather(location, city)
        
        response_data = {
            "location": location,
            "city": city,
            "weather_data": weather_data,
            "forecast": forecast
        }
        
        return api_response(
            data=response_data,
            message="天气信息获取成功"
        )
        
    except ValueError as e:
        logger.error(f"参数错误: {e}")
        return api_response(
            success=False,
            message=f"参数错误: {str(e)}",
            error_code="INVALID_PARAMETER"
        ), 400
    except RuntimeError as e:
        logger.error(f"天气API调用失败: {e}")
        return api_response(
            success=False,
            message=f"天气API调用失败: {str(e)}",
            error_code="WEATHER_API_ERROR"
        ), 502
    except Exception as e:
        logger.error(f"获取天气信息失败: {e}")
        return api_response(
            success=False,
            message=f"天气信息获取失败: {str(e)}",
            error_code="WEATHER_DATA_ERROR"
        ), 500

@app.route('/api/realtime/<attraction>', methods=['GET'])
@error_handler
def get_realtime_info(attraction):
    """获取景点实时信息"""
    if not mcp_manager:
        return api_response(
            success=False,
            message="实时信息服务不可用",
            error_code="MCP_SERVICE_UNAVAILABLE"
        ), 503
    
    query = request.args.get('query', f'{attraction}实时信息')
    
    try:
        # 获取综合实时信息
        realtime_data = mcp_manager.get_comprehensive_info(attraction)
        
        # 格式化响应
        formatted_response = mcp_manager.format_response(realtime_data, query)
        
        response_data = {
            "attraction": attraction,
            "realtime_data": realtime_data,
            "formatted_info": formatted_response,
            "query": query,
            "services_used": realtime_data.get('services_used', [])
        }
        
        return api_response(
            data=response_data,
            message="实时信息获取成功"
        )
        
    except Exception as e:
        logger.error(f"获取实时信息失败: {e}")
        return api_response(
            success=False,
            message="实时信息获取失败",
            error_code="REALTIME_DATA_ERROR"
        ), 500

@app.route('/api/attractions', methods=['GET'])
@error_handler
def get_attractions():
    """获取景点列表"""
    query = request.args.get('query', '')
    category = request.args.get('category', '')
    limit = int(request.args.get('limit', 20))
    
    try:
        # 从配置获取景点列表
        attractions = Config.SHANGHAI_ATTRACTIONS
        
        # 如果有查询参数，进行过滤
        if query:
            attractions = [
                attr for attr in attractions 
                if query.lower() in attr.lower()
            ]
        
        # 分类过滤（这里可以扩展更复杂的分类逻辑）
        if category:
            # 简单的分类匹配
            category_keywords = {
                'museum': ['博物馆', '美术馆', '展览'],
                'park': ['公园', '植物园', '森林'],
                'shopping': ['路', '商场', '购物'],
                'landmark': ['塔', '大厦', '中心', '外滩']
            }
            
            if category in category_keywords:
                keywords = category_keywords[category]
                attractions = [
                    attr for attr in attractions
                    if any(keyword in attr for keyword in keywords)
                ]
        
        # 限制数量
        attractions = attractions[:limit]
        
        response_data = {
            "attractions": attractions,
            "total_count": len(attractions),
            "query": query,
            "category": category,
            "districts": Config.SHANGHAI_DISTRICTS
        }
        
        return api_response(
            data=response_data,
            message="景点列表获取成功"
        )
        
    except Exception as e:
        logger.error(f"获取景点列表失败: {e}")
        return api_response(
            success=False,
            message="景点数据获取失败",
            error_code="ATTRACTIONS_DATA_ERROR"
        ), 500

@app.route('/api/planning', methods=['POST'])
@error_handler
@validate_request(['attractions'])
def plan_route():
    """路线规划接口"""
    if not tourism_assistant:
        return api_response(
            success=False,
            message="路线规划服务不可用",
            error_code="PLANNING_SERVICE_UNAVAILABLE"
        ), 503
    
    data = request.get_json()
    attractions = data.get('attractions', [])
    start_time = data.get('start_time', '09:00')
    preferences = data.get('preferences', [])
    
    try:
        # 使用助手的路线规划功能
        route_plan = tourism_assistant.plan_route(attractions, start_time)
        
        # 获取建议景点（如果用户提供了偏好）
        suggestions = tourism_assistant.get_attraction_suggestions(preferences) if preferences else []
        
        response_data = {
            "route_plan": route_plan,
            "suggested_attractions": suggestions,
            "planning_params": {
                "start_time": start_time,
                "preferences": preferences,
                "total_attractions": len(attractions)
            }
        }
        
        return api_response(
            data=response_data,
            message="路线规划成功"
        )
        
    except Exception as e:
        logger.error(f"路线规划失败: {e}")
        return api_response(
            success=False,
            message="路线规划失败",
            error_code="ROUTE_PLANNING_ERROR"
        ), 500

@app.route('/api/traffic/attraction/<string:attraction>', methods=['GET'])
@error_handler
def query_attraction_traffic_api(attraction):
    """查询景点周边交通状况 - MCP框架"""
    if not mcp_manager:
        return api_response(
            success=False,
            message="MCP服务不可用",
            error_code="MCP_SERVICE_UNAVAILABLE"
        ), 503
    
    try:
        # 通过MCP框架获取景点交通状况
        result = mcp_manager.traffic_service.get_traffic_info(attraction)
        
        return api_response(
            data=result,
            message="景点交通查询成功"
        )
        
    except Exception as e:
        logger.error(f"景点交通查询失败: {e}")
        return api_response(
            success=False,
            message=f"景点交通查询失败: {str(e)}",
            error_code="ATTRACTION_TRAFFIC_QUERY_ERROR"
        ), 500

@app.route('/api/traffic/route', methods=['POST'])
@error_handler
@validate_request(['attractions'])
def analyze_route_traffic():
    """分析路线交通状况 - MCP框架"""
    if not mcp_manager:
        return api_response(
            success=False,
            message="MCP服务不可用",
            error_code="MCP_SERVICE_UNAVAILABLE"
        ), 503
    
    data = request.get_json()
    attractions = data.get('attractions', [])
    
    if not attractions or not isinstance(attractions, list):
        return api_response(
            success=False,
            message="attractions参数必须是非空数组",
            error_code="INVALID_ATTRACTIONS_PARAMETER"
        ), 400
    
    try:
        # 通过MCP框架分析路线交通
        result = mcp_manager.get_route_traffic_analysis(attractions)
        
        return api_response(
            data=result,
            message=f"路线交通分析完成，涉及{len(attractions)}个景点"
        )
        
    except Exception as e:
        logger.error(f"路线交通分析失败: {e}")
        return api_response(
            success=False,
            message=f"路线分析失败: {str(e)}",
            error_code="ROUTE_TRAFFIC_ANALYSIS_ERROR"
        ), 500



@app.route('/api/history/<user_id>', methods=['GET'])
@error_handler
def get_chat_history(user_id):
    """获取用户对话历史"""
    limit = int(request.args.get('limit', 10))
    
    try:
        history = user_sessions.get(user_id, [])
        
        # 限制返回数量
        history = history[-limit:] if limit > 0 else history
        
        response_data = {
            "user_id": user_id,
            "history": history,
            "total_conversations": len(user_sessions.get(user_id, []))
        }
        
        return api_response(
            data=response_data,
            message="历史记录获取成功"
        )
        
    except Exception as e:
        logger.error(f"获取历史记录失败: {e}")
        return api_response(
            success=False,
            message="历史记录获取失败",
            error_code="HISTORY_RETRIEVAL_ERROR"
        ), 500

@app.route('/api/config', methods=['GET'])
@error_handler
def get_config():
    """获取系统配置信息（公开部分）"""
    try:
        config_info = {
            "system_features": {
                "enhanced_mode": assistant_initialized,
                "weather_service": Config.ENABLE_WEATHER_SERVICE,
                "crowd_service": Config.ENABLE_CROWD_SERVICE,
                "traffic_service": Config.ENABLE_TRAFFIC_SERVICE,
                "route_planning": Config.ENABLE_ROUTE_PLANNING
            },
            "limits": {
                "max_query_length": Config.MAX_QUERY_LENGTH,
                "max_search_results": Config.MAX_SEARCH_RESULTS,
                "requests_per_minute": API_RATE_LIMIT['requests_per_minute']
            },
            "supported_districts": Config.SHANGHAI_DISTRICTS,
            "ai_model": Config.DOUBAO_MODEL,
            "version": "1.0.0"
        }
        
        return api_response(
            data=config_info,
            message="配置信息获取成功"
        )
        
    except Exception as e:
        logger.error(f"获取配置失败: {e}")
        return api_response(
            success=False,
            message="配置信息获取失败",
            error_code="CONFIG_RETRIEVAL_ERROR"
        ), 500

# =================== 错误处理 ===================

@app.errorhandler(404)
def not_found(error):
    return api_response(
        success=False,
        message="请求的端点不存在",
        error_code="ENDPOINT_NOT_FOUND"
    ), 404

@app.errorhandler(405)
def method_not_allowed(error):
    return api_response(
        success=False,
        message="不支持的HTTP方法",
        error_code="METHOD_NOT_ALLOWED"
    ), 405

@app.errorhandler(429)
def rate_limit_exceeded(error):
    return api_response(
        success=False,
        message="请求频率过高，请稍后再试",
        error_code="RATE_LIMIT_EXCEEDED"
    ), 429

@app.errorhandler(500)
def internal_error(error):
    return api_response(
        success=False,
        message="服务器内部错误",
        error_code="INTERNAL_SERVER_ERROR"
    ), 500

# =================== 主程序入口 ===================

if __name__ == '__main__':
    print("🌍 正在启动上海旅游AI助手API服务器...")
    
    # 初始化服务
    if not init_services():
        print("❌ 服务初始化失败，API服务器无法启动")
        exit(1)
    
    print("✅ 服务初始化成功")
    print("📡 API端点列表:")
    print("  GET  /                    - 健康检查")
    print("  GET  /api/status          - 服务状态")
    print("  POST /api/chat            - 智能对话")
    print("  GET  /api/weather/<name>  - 天气信息")
    print("  GET  /api/realtime/<name> - 实时信息")
    print("  GET  /api/attractions     - 景点列表")
    print("  POST /api/planning        - 路线规划")
    print("  GET  /api/history/<id>    - 对话历史")
    print("  GET  /api/config          - 系统配置")
    print("  🚦 交通MCP服务API:")
    print("  GET      /api/traffic/attraction/<>  - 景点周边交通(MCP)")
    print("  POST     /api/traffic/route          - 路线交通分析(MCP)")
    
    print("\n🚀 启动Flask开发服务器...")
    print("🌐 访问地址: http://localhost:5000")
    print("📖 API文档: 请查看README.md中的前端集成指南")
    
    # 启动Flask应用
    app.run(
        host='0.0.0.0',  # 允许外部访问
        port=5000,
        debug=True,      # 开发模式
        threaded=True    # 支持多线程
    )
