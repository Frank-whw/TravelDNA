# MCP框架架构文档

## 🎯 MCP (Model Context Protocol) 框架概述

MCP框架是上海旅游AI Agent的核心组成部分，提供统一的外部服务接入标准。框架包含四个主要MCP服务：天气MCP、人流MCP、交通MCP和导航MCP，共同为Agent提供实时的多维度信息支持。

## 🏗️ 架构图

```
┌─────────────────────────────────────────────────────────┐
│                    AI Agent                              │
│                  (model.py)                             │
└─────────────────┬───────────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────────────┐
│                MCP Framework                            │
│              (mcp_services.py)                          │
│  ┌─────────────────────────────────────────────────────┐ │
│  │            MCPServiceManager                        │ │
│  │  ┌──────────┬───────────┬──────────┬─────────────────┐ │ │
│  │  │          │           │          │                 │ │ │
│  │  ▼          ▼           ▼          ▼                 │ │ │
│  │  🌤️         👥          🚦         🧭                │ │ │
│  │Weather    Crowd      Traffic   Navigation           │ │ │
│  │MCP        MCP        MCP        MCP                 │ │ │
│  │Service    Service    Service    Service             │ │ │
│  └─────────────────────────────────────────────────────┘ │
└─────────────┬───────────────────────────────────────────┘
              │
┌─────────────▼───────────────────────────────────────────┐
│                External APIs                            │
│  ┌──────────┬───────────┬──────────┬──────────────────┐ │
│  │高德天气API │模拟人流API │高德交通API│高德导航路径规划API │ │
│  │          │          │          │                  │ │
│  │• 实时天气  │• 人流预测  │• 道路交通 │• 驾车路径规划      │ │
│  │• 天气预报  │• 拥挤度    │• 路线分析 │• 多目的地规划      │ │
│  │• 气象建议  │• 最佳时间  │• 出行建议 │• 多种策略选择      │ │
│  └──────────┴───────────┴──────────┴──────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

## 📋 MCP服务详细说明

### 🌤️ WeatherMCPService (天气MCP)
- **功能**: 提供实时天气和天气预报
- **API**: 高德地图天气API
- **主要方法**:
  - `get_weather(attraction, city)` - 获取实时天气
  - `get_weather_forecast(city, days)` - 获取天气预报
- **返回数据**: 温度、天气状况、湿度、风力、出行建议

### 👥 CrowdMCPService (人流MCP)
- **功能**: 提供景点人流量信息
- **API**: 模拟API（可扩展为真实人流API）
- **主要方法**:
  - `get_crowd_info(attraction)` - 获取人流状况
- **返回数据**: 拥挤程度、等待时间、最佳游览时间

### 🚦 TrafficMCPService (交通MCP)
- **功能**: 提供实时交通态势和路线分析
- **API**: 高德地图交通态势API
- **集成模块**: `traffic_service.py`
- **主要方法**:
  - `get_traffic_info(attraction, origin)` - 获取景点交通状况
  - `get_route_traffic_analysis(attractions)` - 分析路线交通
- **返回数据**: 交通状况、拥堵程度、出行建议、最佳交通方式

### 🧭 NavigationMCPService (导航MCP)
- **功能**: 提供驾车路径规划和导航服务
- **API**: 高德地图路径规划API
- **API密钥**: 95dfa5cfda994230af9b6ab64de4b84b
- **主要方法**:
  - `get_route_planning(origin, destination, strategy)` - 获取单点路径规划
  - `get_multi_destination_planning(origin, destinations)` - 多目的地路径规划
- **支持策略**: 速度优先、费用优先、躲避拥堵、不走高速、少收费等15种策略
- **返回数据**: 距离、时长、过路费、红绿灯数量、详细导航步骤、限行状态

## 🔄 MCP框架工作流程

### 1. 初始化阶段
```python
# MCPServiceManager初始化
mcp_manager = MCPServiceManager()
├── weather_service = WeatherMCPService()
├── crowd_service = CrowdMCPService()  
├── traffic_service = TrafficMCPService()
│   └── 集成 TrafficService(Config.AMAP_TRAFFIC_API_KEY)
└── navigation_service = NavigationMCPService()
    └── 集成 高德路径规划API(Config.AMAP_NAVIGATION_API_KEY)
```

### 2. 数据获取阶段
```python
# Agent请求综合信息（包含导航）
comprehensive_info = mcp_manager.get_comprehensive_info("外滩", include_navigation=True)
├── weather_info = weather_service.get_weather("外滩")
├── crowd_info = crowd_service.get_crowd_info("外滩")
├── traffic_info = traffic_service.get_traffic_info("外滩")
├── navigation_info = navigation_service.get_route_planning("市中心", "外滩")
└── forecast_info = weather_service.get_weather_forecast("上海", 3)
```

### 3. 信息整合阶段
```python
# MCP数据统一格式化
result = {
    "attraction": "外滩",
    "weather": weather_info,      # 天气MCP数据
    "crowd": crowd_info,          # 人流MCP数据
    "traffic": traffic_info,      # 交通MCP数据
    "navigation": navigation_info, # 导航MCP数据
    "weather_forecast": forecast_info,
    "services_used": ["weather", "crowd", "traffic", "navigation", "weather_forecast"]
}
```

### 4. Agent智能回答
```python
# Agent集成MCP数据生成回答
enhanced_prompt = create_enhanced_prompt(query, knowledge_context, mcp_results)
ai_response = call_doubao_api(enhanced_prompt)
final_response = ai_response + formatted_mcp_info
```

## 🔌 API端点集成

### RESTful API端点
- `GET /api/traffic/attraction/<景点>` - 景点交通查询(MCP)
- `POST /api/traffic/route` - 路线交通分析(MCP)
- `POST /api/navigation/route` - 单点导航路径规划(MCP)
- `POST /api/navigation/multi-destination` - 多目的地路径规划(MCP)
- `GET /api/navigation/strategies` - 获取导航策略(MCP)
- `GET /api/navigation/coordinates` - 获取景点坐标(MCP)
- `GET /api/weather/<景点>` - 天气信息(MCP)
- `GET /api/realtime/<景点>` - 综合实时信息(MCP)

### 内部MCP调用
```python
# 通过MCP框架获取交通信息
traffic_result = mcp_manager.traffic_service.get_traffic_info("外滩")

# 通过MCP框架分析路线
route_analysis = mcp_manager.get_route_traffic_analysis(["外滩", "东方明珠"])

# 通过MCP框架获取导航路径规划
navigation_result = mcp_manager.get_navigation_planning("外滩", "东方明珠")

# 通过MCP框架获取多目的地导航
multi_nav = mcp_manager.get_multi_destination_planning("外滩", ["豫园", "新天地"])

# 通过MCP框架获取综合信息（包含导航）
all_info = mcp_manager.get_comprehensive_info("外滩", include_navigation=True)
```

## 📊 配置管理

### 统一配置 (config.py)
```python
# 天气MCP配置
AMAP_WEATHER_API_KEY = "eabe457b791e74946b2aeb6a9106b17a"
AMAP_WEATHER_URL = "https://restapi.amap.com/v3/weather/weatherInfo"

# 交通MCP配置  
AMAP_TRAFFIC_API_KEY = "425125fef7e244aa380807946ec48776"
AMAP_TRAFFIC_URL = "https://restapi.amap.com/v3/traffic/status/road"

# 导航MCP配置
AMAP_NAVIGATION_API_KEY = "95dfa5cfda994230af9b6ab64de4b84b"
AMAP_NAVIGATION_URL = "https://restapi.amap.com/v5/direction/driving"
NAVIGATION_STRATEGIES = {
    "default": 32, "avoid_congestion": 33, "no_highway": 35, ...
}

# 景点配置
SHANGHAI_ATTRACTION_ROADS = {...}        # 景点道路映射
SHANGHAI_ATTRACTION_DISTRICTS = {...}    # 景点区域映射
SHANGHAI_ATTRACTION_COORDINATES = {...}  # 景点经纬度映射
```

## 🎯 核心优势

### 1. 统一接口标准
- 所有MCP服务继承自 `MCPService` 基类
- 统一的数据格式和错误处理
- 标准化的服务发现和管理

### 2. 模块化设计
- 每个MCP服务独立开发和维护
- 易于扩展新的MCP服务（如导航MCP）
- 服务间解耦，故障隔离

### 3. 智能集成
- Agent自动整合多MCP数据
- 基于实时信息动态调整建议
- 上下文感知的智能回答

### 4. 高可用性
- Fallback机制保证服务可用性
- 错误恢复和降级策略
- 缓存机制提高响应速度

## 🚀 扩展性

### 已实现MCP服务

#### 🧭 NavigationMCPService (导航MCP) - ✅ 已实现
```python
class NavigationMCPService(MCPService):
    """导航MCP服务 - 已集成高德地图路径规划API"""
    
    def get_route_planning(self, origin, destination, strategy="default"):
        """获取单点路径规划"""
        # 支持15种导航策略
        # 返回距离、时长、过路费、红绿灯、详细步骤
    
    def get_multi_destination_planning(self, origin, destinations):
        """获取多目的地路径规划"""
        # 支持最多16个途经点
        # 自动计算最优路线和时间安排
    
    def _get_coordinates(self, location):
        """景点名称转经纬度坐标"""
        # 支持40+上海主要景点坐标映射
```

### 未来MCP服务规划

#### 🏨 AccommodationMCPService (住宿MCP) - 扩展
```python
class AccommodationMCPService(MCPService):
    """住宿MCP服务"""
    
    def get_nearby_hotels(self, attraction, price_range):
        """获取附近酒店信息"""
        pass
```

### 集成新MCP服务步骤
1. 继承 `MCPService` 基类
2. 实现标准MCP接口方法  
3. 在 `MCPServiceManager` 中注册
4. 更新Agent集成逻辑
5. 添加相应API端点

## 📈 性能监控

### 关键指标
- MCP服务响应时间
- API调用成功率  
- 数据缓存命中率
- Agent回答质量评分

### 日志记录
```python
logger.info("🚀 MCP服务管理器初始化完成")
logger.info("✅ 交通MCP服务初始化成功") 
logger.warning("⚠️ 获取天气预报失败")
logger.error("❌ 交通API调用异常")
```

## 🧪 测试验证

### 自动化测试
- `test_mcp_traffic.py` - 交通MCP框架测试
- `test_navigation_mcp.py` - 导航MCP服务测试 (新增)
- 覆盖所有MCP服务接口
- Agent集成端到端验证

### 测试结果
```
📊 导航MCP测试结果总结
  基础导航功能              ✅ 通过
  导航策略测试              ✅ 通过
  多目的地规划              ✅ 通过
  坐标处理功能              ✅ 通过
  MCP框架集成              ✅ 通过
  错误处理机制              ✅ 通过
  性能测试                ✅ 通过
📈 通过率: 7/7 (100.0%)
```

---

## 📝 总结

MCP框架成功实现了：
- **标准化**: 统一的MCP服务接口和数据格式
- **模块化**: 天气、人流、交通、导航四大MCP服务独立运行
- **智能化**: Agent深度集成MCP数据，提供智能建议
- **完整性**: 涵盖出行全链路：天气→人流→交通→导航
- **可靠性**: 完善的错误处理和降级机制

导航MCP作为框架的最新组成部分，与天气MCP、人流MCP、交通MCP协同工作，为上海旅游AI Agent提供了完整的出行规划和导航服务，形成了从信息查询到路径规划的闭环体验。

*最后更新: 2025-01-27*  
*架构版本: MCP Framework v1.1 (新增导航MCP)*
