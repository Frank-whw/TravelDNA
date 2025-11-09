#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能旅游Agent API服务器
提供AI驱动的旅游规划和问答服务
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from dotenv import load_dotenv
import json
import time
from datetime import datetime
import sys
import logging

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 加载环境变量
load_dotenv()

# 导入自定义模块
try:
    from enhanced_travel_agent import EnhancedTravelAgent as TravelAgentService, TravelPreference
except ImportError as e:
    print(f"Warning: Could not import enhanced_travel_agent module: {e}")
    TravelAgentService = None
    TravelPreference = None

try:
    from recommand import RecommendationPlanner
except ImportError as e:
    print(f"Warning: Could not import recommand module: {e}")
    RecommendationPlanner = None

from config import Config

# 创建Flask应用
app = Flask(__name__)
app.config.from_object(Config)
app.json.ensure_ascii = False

logger = logging.getLogger(__name__)

# 启用CORS
CORS(app, resources={r"/api/*": {"origins": "*"}})

# 全局变量存储计划和服务实例
travel_plans = {}
agent_service = None
planner_service = None

# 初始化服务
if TravelAgentService:
    try:
        agent_service = TravelAgentService()
        print("EnhancedTravelAgent initialized successfully")
    except Exception as e:
        print(f"Failed to initialize EnhancedTravelAgent: {e}")
        agent_service = None
else:
    print("EnhancedTravelAgent not available, using mock responses")
    agent_service = None

if RecommendationPlanner:
    try:
        planner_service = RecommendationPlanner()
        print("RecommendationPlanner initialized successfully")
    except Exception as e:
        print(f"Failed to initialize RecommendationPlanner: {e}")
        planner_service = None
else:
    print("RecommendationPlanner not available, skip initialization")

# API路由前缀
API_PREFIX = '/api/v1'

@app.route(f'{API_PREFIX}/health', methods=['GET'])
def health_check():
    """健康检查接口"""
    return jsonify({
        'status': 'success',
        'message': 'Agent服务运行正常',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0'
    })

@app.route(f'{API_PREFIX}/chat', methods=['POST'])
def chat():
    """AI聊天接口"""
    try:
        data = request.get_json()
        if not data or 'message' not in data:
            return jsonify({
                'status': 'error',
                'message': '请提供消息内容',
                'errorCode': 'MISSING_MESSAGE'
            }), 400
        
        user_message = data['message']
        context = data.get('context', {})
        
        # 使用增强版Agent处理请求
        if agent_service:
            try:
                # 使用增强版思考链系统处理用户请求，返回思考过程
                result = agent_service.process_user_request(
                    user_message, 
                    user_id=context.get('user_id', 'default'), 
                    show_thoughts=False,
                    return_thoughts=True
                )
                
                if isinstance(result, dict):
                    response = result['response']
                    thoughts = result.get('thoughts', [])
                    extracted_info = result.get('extracted_info', {})
                else:
                    response = result
                    thoughts = []
                    extracted_info = {}
                
                suggestions = ["制定旅游计划", "查询景点信息", "天气查询", "路线规划"]
            except Exception as e:
                print(f"增强版Agent处理失败: {e}")
                # 降级到基础回复逻辑
                response = f"我理解您的需求，正在为您规划旅游攻略。由于系统繁忙，请稍后再试或重新描述您的需求。"
                thoughts = []
                extracted_info = {}
                suggestions = ["制定旅游计划", "查询景点信息", "天气查询"]
        else:
            # 基础智能回复逻辑（当Agent不可用时）
            if '天气' in user_message:
                response = "根据最新天气预报，今天是个适合出行的好天气！建议您选择户外景点游览。如需详细天气信息，我可以为您查询具体地点的天气状况。"
                suggestions = ["外滩观光", "豫园游览", "人民广场散步", "查询具体天气"]
            elif '交通' in user_message:
                response = "我可以为您制定行程、推荐景点和查询天气等信息。若需规划出行路线，我也可以结合景点开放时间与人流情况为您安排合理行程。"
                suggestions = ["制定旅游计划", "查询景点信息", "天气查询"]
            elif '美食' in user_message:
                response = "上海有很多特色美食！我推荐尝试小笼包、生煎包、本帮菜等。可以为您推荐附近的特色餐厅。"
                suggestions = ["南翔小笼包", "大壶春生煎", "老正兴菜馆", "附近美食推荐"]
            elif '规划' in user_message or '计划' in user_message or '路线' in user_message or '行程' in user_message:
                response = "我可以为您制定个性化的旅游计划！请告诉我您的出发地、想去的景点，以及您的偏好（如时间、预算、兴趣等），我会为您规划最佳路线。"
                suggestions = ["创建旅游计划", "景点推荐", "路线优化", "预算规划"]
            elif '景点' in user_message or '推荐' in user_message:
                response = "我可以根据您的兴趣推荐合适的景点！上海有外滩、东方明珠、豫园、南京路等著名景点。您偏好哪种类型的景点呢？"
                suggestions = ["历史文化景点", "现代建筑景观", "购物娱乐区域", "自然风光"]
            else:
                response = f"我理解您想了解\"{user_message}\"。作为您的智能旅游助手，我可以为您提供：\n\n🗺️ 个性化旅游规划\n🌤️ 实时天气信息\n🍜 美食景点推荐\n📊 人流量预测\n\n请告诉我您的具体需求，我会为您提供最专业的建议！"
                suggestions = ["制定旅游计划", "查询景点信息", "天气查询"]
            
            # 基础回复时没有思考过程
            thoughts = []
            extracted_info = {}
        
        ai_response = {
            'message': response,
            'suggestions': suggestions,
            'type': 'text',
            'timestamp': datetime.now().isoformat(),
            'thoughts': thoughts,
            'extracted_info': extracted_info
        }
        
        return jsonify({
            'status': 'success',
            'data': ai_response
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'处理请求时发生错误: {str(e)}',
            'errorCode': 'INTERNAL_ERROR'
        }), 500

@app.route(f'{API_PREFIX}/travel-plan', methods=['POST'])
def create_travel_plan():
    """创建旅游计划接口"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'status': 'error',
                'message': '请提供计划参数',
                'errorCode': 'MISSING_DATA'
            }), 400
        
        # 提取参数
        origin = data.get('origin')
        destinations = data.get('destinations', [])
        preferences_data = data.get('preferences', {})
        
        if not origin or not destinations:
            return jsonify({
                'status': 'error',
                'message': '请提供出发地和目的地',
                'errorCode': 'MISSING_LOCATIONS'
            }), 400
        
        # 使用增强版TravelAgentService或模拟服务
        if agent_service:
            try:
                # 构建用户输入
                user_input = f"我想从{origin}出发，去{', '.join(destinations)}旅游"
                if preferences_data:
                    if preferences_data.get('travel_days'):
                        user_input += f"，计划{preferences_data['travel_days']}天"
                    if preferences_data.get('budget'):
                        user_input += f"，预算{preferences_data['budget']}元"
                
                # 使用增强版Agent处理
                result = agent_service.process_user_request(user_input, user_id="api_user", show_thoughts=False, return_thoughts=True)
                
                if isinstance(result, dict):
                    response = result['response']
                    thoughts = result.get('thoughts', [])
                    extracted_info = result.get('extracted_info', {})
                else:
                    response = result
                    thoughts = []
                    extracted_info = {}
                
                # 构建旅游计划响应
                plan_id = f'plan_{int(datetime.now().timestamp())}'
                travel_plan = {
                    'id': plan_id,
                    'origin': origin,
                    'destinations': destinations,
                    'response': response,
                    'thoughts': thoughts,  # 添加思考过程
                    'extracted_info': extracted_info,  # 添加提取的信息
                    'pois': [],  # 可以从agent的实时数据中提取
                    'route_segments': [],
                    'total_distance': len(destinations) * 3.5,
                    'total_duration': len(destinations) * 120,
                    'total_cost': len(destinations) * 25.0,
                    'weather_compatibility': 85.0,
                    'crowd_score': 75.0,
                    'overall_score': 88.0,
                    'recommendations': [
                        '已为您制定基于实时数据的智能旅游攻略',
                        '建议关注天气变化，合理安排行程',
                        '推荐使用公共交通，环保便捷'
                    ],
                    'adjustments': [],
                    'created_at': datetime.now().isoformat()
                }
            except Exception as e:
                logger.error(f"增强版Agent创建计划失败: {e}")
                # 降级到模拟功能
                travel_plan = self._create_fallback_plan(origin, destinations, preferences_data)
        else:
            # 模拟创建旅游计划
            travel_plan = self._create_fallback_plan(origin, destinations, preferences_data)
        
        # 存储计划
        travel_plans[travel_plan['id']] = travel_plan
        
        return jsonify({
            'status': 'success',
            'data': travel_plan
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'创建旅游计划时发生错误: {str(e)}',
            'errorCode': 'PLAN_CREATION_ERROR'
        }), 500

@app.route(f'{API_PREFIX}/poi/search', methods=['GET'])
def search_poi():
    """POI搜索接口"""
    try:
        query = request.args.get('q', '')
        city = request.args.get('city', '上海')
        category = request.args.get('category', '')
        
        if not query:
            return jsonify({
                'status': 'error',
                'message': '请提供搜索关键词',
                'errorCode': 'MISSING_QUERY'
            }), 400
        
        # 使用真实服务或模拟搜索
        if agent_service and hasattr(agent_service, 'poi_database'):
            # 从数据库中搜索匹配的POI
            matching_pois = []
            for poi_name, poi_info in agent_service.poi_database.items():
                if query.lower() in poi_name.lower() or query.lower() in poi_info.category.lower():
                    matching_pois.append({
                        'id': f'poi_{len(matching_pois)+1:03d}',
                        'name': poi_info.name,
                        'address': poi_info.address,
                        'rating': poi_info.rating,
                        'category': poi_info.category,
                        'description': poi_info.description,
                        'coordinates': poi_info.coordinates,
                        'opening_hours': poi_info.opening_hours,
                        'ticket_price': poi_info.ticket_price,
                        'visit_duration': poi_info.visit_duration,
                        'crowd_level': poi_info.crowd_level.value if hasattr(poi_info.crowd_level, 'value') else poi_info.crowd_level,
                        'weather_dependency': poi_info.weather_dependency
                    })
            
            if matching_pois:
                return jsonify({
                    'status': 'success',
                    'data': matching_pois,
                    'count': len(matching_pois)
                })
        
        # 模拟POI搜索结果
        pois = [
            {
                'id': 'poi_001',
                'name': f'{query}相关景点1',
                'address': f'{city}市中心区域',
                'rating': 4.5,
                'category': category or '景点',
                'description': f'这是一个与{query}相关的热门景点，值得一游',
                'coordinates': {'lat': 31.2304, 'lng': 121.4737},
                'opening_hours': '09:00-17:00',
                'ticket_price': 50.0,
                'visit_duration': 120,
                'crowd_level': 'medium',
                'weather_dependency': False
            },
            {
                'id': 'poi_002', 
                'name': f'{query}相关景点2',
                'address': f'{city}历史文化区',
                'rating': 4.2,
                'category': category or '景点',
                'description': f'另一个与{query}相关的推荐地点，环境优美',
                'coordinates': {'lat': 31.2396, 'lng': 121.4994},
                'opening_hours': '08:30-18:00',
                'ticket_price': 30.0,
                'visit_duration': 90,
                'crowd_level': 'low',
                'weather_dependency': True
            }
        ]
        
        return jsonify({
            'status': 'success',
            'data': pois,
            'count': len(pois)
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'搜索POI时发生错误: {str(e)}',
            'errorCode': 'POI_SEARCH_ERROR'
        }), 500

@app.route(f'{API_PREFIX}/travel/preferences/questions', methods=['GET'])
def get_preference_questions():
    """获取偏好问题"""
    try:
        questions = [
            {
                'id': 'travel_style',
                'question': '您偏好什么样的旅行风格？',
                'type': 'single_choice',
                'options': ['休闲放松', '文化探索', '冒险刺激', '美食体验', '购物娱乐']
            },
            {
                'id': 'budget_range',
                'question': '您的预算范围是多少？',
                'type': 'single_choice',
                'options': ['100-300元', '300-500元', '500-1000元', '1000元以上']
            },
            {
                'id': 'time_preference',
                'question': '您偏好什么时间出行？',
                'type': 'single_choice',
                'options': ['早上', '上午', '下午', '傍晚', '晚上']
            },
            {
                'id': 'crowd_tolerance',
                'question': '您对人流量的容忍度如何？',
                'type': 'single_choice',
                'options': ['喜欢热闹', '适中即可', '偏好安静']
            },
            {
                'id': 'weather_dependency',
                'question': '天气对您的出行影响大吗？',
                'type': 'single_choice',
                'options': ['影响很大', '有一定影响', '基本不影响']
            }
        ]
        
        return jsonify({
            'status': 'success',
            'data': questions
        })
    
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route(f'{API_PREFIX}/travel/plan/<plan_id>', methods=['GET'])
def get_travel_plan(plan_id):
    """获取旅游计划详情"""
    try:
        if plan_id not in travel_plans:
            return jsonify({
                'status': 'error',
                'message': '计划不存在'
            }), 404
        
        plan = travel_plans[plan_id]
        return jsonify({
            'status': 'success',
            'data': plan
        })
    
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route(f'{API_PREFIX}/travel/plan/<plan_id>/adjust', methods=['POST'])
def adjust_travel_plan(plan_id):
    """调整旅游计划"""
    try:
        if plan_id not in travel_plans:
            return jsonify({
                'status': 'error',
                'message': '计划不存在'
            }), 404
        
        data = request.get_json()
        adjustments = data.get('adjustments', {})
        
        plan = travel_plans[plan_id]
        
        # 应用调整
        if 'budget' in adjustments:
            # 根据预算调整推荐
            budget = adjustments['budget']
            if budget < 200:
                plan['recommendations'].append('推荐选择免费或低价景点')
            elif budget > 1000:
                plan['recommendations'].append('可以考虑高端体验项目')
        
        if 'time_preference' in adjustments:
            time_pref = adjustments['time_preference']
            if time_pref == '早上':
                plan['recommendations'].append('建议早上8点前出发，避开人流')
            elif time_pref == '傍晚':
                plan['recommendations'].append('傍晚时分景色更美，适合拍照')
        
        if 'crowd_tolerance' in adjustments:
            crowd_pref = adjustments['crowd_tolerance']
            if crowd_pref == '偏好安静':
                plan['recommendations'].append('建议选择工作日出行，避开周末人流')
        
        # 更新计划
        plan['adjustments'] = adjustments
        plan['updated_at'] = datetime.now().isoformat()
        travel_plans[plan_id] = plan
        
        return jsonify({
            'status': 'success',
            'data': plan,
            'message': '计划已成功调整'
        })
    
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route(f'{API_PREFIX}/travel/plan/<plan_id>/optimize', methods=['POST'])
def optimize_route(plan_id):
    """优化路线"""
    try:
        if plan_id not in travel_plans:
            return jsonify({
                'status': 'error',
                'message': '计划不存在'
            }), 404
        
        plan = travel_plans[plan_id]
        
        # 模拟路线优化
        original_distance = plan.get('total_distance', 0)
        original_duration = plan.get('total_duration', 0)
        
        # 优化后减少10-20%的距离和时间
        optimized_distance = original_distance * 0.85
        optimized_duration = original_duration * 0.9
        
        plan['total_distance'] = optimized_distance
        plan['total_duration'] = optimized_duration
        plan['overall_score'] = min(plan.get('overall_score', 85) + 5, 100)
        
        if 'recommendations' not in plan:
            plan['recommendations'] = []
        plan['recommendations'].append('路线已优化，节省了15%的行程时间')
        
        plan['optimized_at'] = datetime.now().isoformat()
        travel_plans[plan_id] = plan
        
        return jsonify({
            'status': 'success',
            'data': plan,
            'message': '路线优化完成'
        })
    
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route(f'{API_PREFIX}/travel/weather', methods=['GET'])
def get_weather_info():
    """获取天气信息"""
    try:
        location = request.args.get('location', '上海')
        
        # 模拟天气数据
        weather_data = {
            'location': location,
            'current': {
                'temperature': 22,
                'condition': '晴朗',
                'humidity': 65,
                'wind_speed': 12,
                'visibility': 10
            },
            'forecast': [
                {'date': '今天', 'high': 25, 'low': 18, 'condition': '晴朗'},
                {'date': '明天', 'high': 23, 'low': 16, 'condition': '多云'},
                {'date': '后天', 'high': 20, 'low': 14, 'condition': '小雨'}
            ],
            'travel_advice': '今天天气晴朗，适合户外活动和观光'
        }
        
        return jsonify({
            'status': 'success',
            'data': weather_data
        })
    
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route(f'{API_PREFIX}/travel/traffic', methods=['GET'])
def get_traffic_info():
    """获取交通信息"""
    return jsonify({
        'status': 'error',
        'message': '请求的资源不存在',
        'errorCode': 'NOT_FOUND'
    }), 404

@app.route(f'{API_PREFIX}/travel/crowd', methods=['GET'])
def get_crowd_info():
    """获取人流信息"""
    try:
        location = request.args.get('location', '外滩')
        
        # 模拟人流数据
        crowd_data = {
            'location': location,
            'current_level': 'medium',
            'current_description': '人流适中，游览体验良好',
            'hourly_forecast': [
                {'hour': '09:00', 'level': 'low', 'description': '人流较少'},
                {'hour': '11:00', 'level': 'medium', 'description': '人流适中'},
                {'hour': '14:00', 'level': 'high', 'description': '人流较多'},
                {'hour': '17:00', 'level': 'medium', 'description': '人流适中'},
                {'hour': '19:00', 'level': 'low', 'description': '人流较少'}
            ],
            'best_visit_times': ['09:00-10:00', '19:00-20:00'],
            'crowd_advice': '建议早上或傍晚时段游览，避开下午人流高峰'
        }
        
        return jsonify({
            'status': 'success',
            'data': crowd_data
        })
    
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route(f'{API_PREFIX}/shanghai/dataset', methods=['GET'])
def get_shanghai_dataset():
    """获取上海旅游数据占位信息"""
    if not planner_service:
        return jsonify({
            'status': 'error',
            'message': '推荐引擎未就绪，无法提供数据预览',
            'errorCode': 'PLANNER_UNAVAILABLE'
        }), 503

    dataset = planner_service.get_dataset_summary()
    return jsonify({
        'status': 'success',
        'data': dataset
    })


@app.route(f'{API_PREFIX}/shanghai/recommendations', methods=['POST'])
def create_shanghai_recommendations():
    """生成基于上海数据的智能推荐行程"""
    if not planner_service:
        return jsonify({
            'status': 'error',
            'message': '推荐引擎未就绪，请稍后重试',
            'errorCode': 'PLANNER_UNAVAILABLE'
        }), 503

    try:
        payload = request.get_json() or {}
    except Exception:
        payload = {}

    try:
        result = planner_service.generate_plan(payload)
        return jsonify({
            'status': 'success',
            'data': result
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'生成推荐方案失败: {str(e)}',
            'errorCode': 'PLANNER_ERROR'
        }), 500

@app.errorhandler(404)
def not_found(error):
    """404错误处理"""
    return jsonify({
        'status': 'error',
        'message': '请求的资源不存在',
        'errorCode': 'NOT_FOUND'
    }), 404

@app.errorhandler(500)
def internal_error(error):
    """500错误处理"""
    return jsonify({
        'status': 'error',
        'message': '服务器内部错误',
        'errorCode': 'INTERNAL_SERVER_ERROR'
    }), 500

def _create_fallback_plan(origin: str, destinations: list, preferences_data: dict = None) -> dict:
    """创建降级旅游计划"""
    plan_id = f'plan_{int(datetime.now().timestamp())}'
    return {
        'id': plan_id,
        'origin': origin,
        'destinations': destinations,
        'pois': [
            {
                'name': dest,
                'address': f'{dest}地址',
                'rating': 4.5,
                'category': '景点',
                'description': f'{dest}是一个著名的旅游景点',
                'visit_duration': 90,
                'crowd_level': 'medium',
                'weather_dependency': False
            } for dest in destinations
        ],
        'route_segments': [],
        'total_distance': len(destinations) * 3.5,
        'total_duration': len(destinations) * 120,
        'total_cost': len(destinations) * 25.0,
        'weather_compatibility': 75.0,
        'crowd_score': 70.0,
        'overall_score': 85.0,
        'recommendations': [
            '建议上午出发，避开人流高峰',
            '携带防晒用品，今日阳光较强',
            '尽量选择相邻景点，减少路程时间'
        ],
        'adjustments': [],
        'created_at': datetime.now().isoformat()
    }

if __name__ == '__main__':
    # 从环境变量获取配置
    host = os.getenv('FLASK_HOST', '0.0.0.0')
    port = int(os.getenv('FLASK_PORT', 5001))  # 使用5001端口避免与Community模块冲突
    debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    
    print(f"🚀 智能旅游Agent服务启动")
    print(f"📍 服务地址: http://{host}:{port}")
    print(f"🔧 调试模式: {debug}")
    print(f"📚 API文档: http://{host}:{port}{API_PREFIX}/health")
    
    app.run(host=host, port=port, debug=debug)