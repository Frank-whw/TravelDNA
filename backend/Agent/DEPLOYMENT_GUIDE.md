# 🚀 智能旅游攻略Agent - 部署与使用指南

## 📋 快速开始

### 1. 环境准备
```bash
# 确保Python 3.8+
python --version

# 安装依赖
pip install -r requirements.txt
```

### 2. API密钥配置
```bash
# 复制配置模板
cp env.example .env

# 编辑.env文件，填入您的API密钥
nano .env  # 或使用其他编辑器
```

在`.env`文件中配置：
```bash
# 高德地图API密钥（必填）
AMAP_WEATHER_API_KEY=您的天气API密钥
AMAP_TRAFFIC_API_KEY=您的交通API密钥
AMAP_NAVIGATION_API_KEY=您的导航API密钥
AMAP_POI_API_KEY=您的POI搜索API密钥

# 可选配置
AMAP_TRAFFIC_SECURITY_KEY=您的交通安全密钥
DEBUG=false
LOG_LEVEL=INFO
```

### 3. 配置验证
```bash
# 验证API密钥配置
python validate_config.py
```

### 4. 启动服务
```bash
# 启动Flask API服务器
python api_server.py
```

服务启动后，访问 `http://localhost:5000` 查看API文档。

## 🤖 智能Agent使用方法

### 方法1: Python直接调用

```python
from intelligent_agent import IntelligentTravelAgent

# 初始化Agent
agent = IntelligentTravelAgent()

# 生成智能攻略
result = agent.generate_intelligent_travel_plan("我想去浦东新区玩，带着孩子")

if result['success']:
    print(f"攻略得分: {result['travel_plan']['overall_score']}/100")
    print("智能建议:")
    for rec in result['final_recommendations']:
        print(f"  • {rec}")
```

### 方法2: API接口调用

```bash
# 创建智能旅游攻略
curl -X POST http://localhost:5000/api/travel-plan/create \
  -H "Content-Type: application/json" \
  -d '{
    "user_query": "明天想去外滩看看，顺便购物",
    "user_id": "test_user"
  }'
```

### 方法3: Web界面集成

```javascript
// 前端调用示例
const response = await fetch('/api/travel-plan/create', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    user_query: "我想去浦东新区玩，带着孩子",
    user_id: "user123"
  })
});

const result = await response.json();
console.log('智能攻略:', result.data);
```

## 🎯 核心API端点

### 1. 智能攻略生成
```
POST /api/travel-plan/create
{
  "user_query": "用户自然语言输入",
  "user_id": "用户ID"
}
```

### 2. POI搜索
```
GET /api/poi/search?keywords=咖啡厅&region=上海
GET /api/poi/around?location=121.484429,31.240791&radius=1000
GET /api/poi/recommend?destination=外滩&travel_type=tourism
```

### 3. 导航规划
```
POST /api/navigation/route
{
  "origin": "人民广场",
  "destination": "外滩",
  "strategy": "default"
}
```

### 4. 系统状态
```
GET /api/status  # 服务状态
GET /api/config  # 系统配置
```

## 🧠 智能分析示例

### 用户输入分析

| 用户输入 | 智能分析结果 |
|---------|-------------|
| "我想去浦东新区玩，带着孩子" | 地点: 浦东 → 景点: 东方明珠、迪士尼... → 活动: 亲子 → MCP: 导航+POI+天气 |
| "明天去外滩，担心下雨" | 地点: 外滩 → 关注: 天气 → MCP: 天气+导航+POI |
| "周末开车去迪士尼" | 地点: 迪士尼 → 方式: 自驾 → MCP: 导航+交通+天气+POI |

### MCP调用决策逻辑

```python
# Agent根据关键词智能决策调用哪些MCP
if "浦东" in user_input:
    # 自动推荐: 东方明珠、陆家嘴、迪士尼等
    call_navigation_mcp()  # 路线规划
    call_poi_mcp()         # 周边推荐
    
if "孩子" in user_input:
    # 识别亲子需求
    call_poi_mcp(type="亲子")  # 亲子场所推荐
    
if "天气" in user_input or "雨" in user_input:
    # 天气关注
    call_weather_mcp()     # 天气检查
```

## 🔧 个性化配置

### 1. 扩展地点关键词
在 `intelligent_agent.py` 中扩展 `location_keywords`:

```python
self.location_keywords.update({
    "新区域": ["景点1", "景点2", "景点3"],
    "自定义地点": ["相关景点列表"]
})
```

### 2. 添加活动类型
扩展 `activity_keywords`:

```python
self.activity_keywords.update({
    "新活动": ["关键词1", "关键词2"],
    "特殊需求": ["相关关键词"]
})
```

### 3. 自定义建议规则
在 `_generate_practical_tips` 中添加自定义建议：

```python
if "特定地点" in analysis["detected_locations"]:
    tips.append("🎯 针对该地点的专门建议")
```

## 📊 监控与维护

### 1. 日志监控
```bash
# 查看实时日志
tail -f logs/agent.log

# 分析错误
grep ERROR logs/agent.log
```

### 2. API配额监控
```python
# 在代码中添加配额检查
def check_api_usage():
    # 检查各API的调用次数和配额
    pass
```

### 3. 性能优化
- API调用缓存
- 并发请求控制
- 响应时间监控

## 🔒 安全建议

### 1. API密钥安全
- ✅ 使用环境变量存储
- ✅ 定期轮换密钥
- ✅ 限制IP访问（生产环境）
- ✅ 监控异常调用

### 2. 服务安全
```bash
# 生产环境建议
export FLASK_ENV=production
export DEBUG=false

# 使用HTTPS
# 配置防火墙
# 设置访问控制
```

### 3. 数据安全
- 用户查询日志脱敏
- 敏感信息加密存储
- 定期备份重要数据

## 🐛 故障排查

### 常见问题

1. **API密钥错误**
```bash
# 验证配置
python validate_config.py

# 检查环境变量
echo $AMAP_WEATHER_API_KEY
```

2. **服务启动失败**
```bash
# 检查端口占用
netstat -an | grep 5000

# 检查依赖
pip list | grep flask
```

3. **API调用失败**
```bash
# 检查网络连接
ping restapi.amap.com

# 查看详细错误日志
python -c "import logging; logging.basicConfig(level=logging.DEBUG)"
```

### 错误代码对照

| 错误码 | 含义 | 解决方案 |
|-------|------|---------|
| 10001 | INVALID_USER_KEY | 检查API密钥配置 |
| 10021 | 配额超限 | 检查调用频率，等待重置 |
| 20001 | 请求参数错误 | 检查请求格式 |

## 🚀 部署到生产环境

### 1. Docker部署
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 5000

CMD ["python", "api_server.py"]
```

### 2. 云服务部署
```bash
# 使用云服务提供商的容器服务
# 配置负载均衡
# 设置自动扩缩容
```

### 3. 监控告警
```yaml
# 配置监控指标
metrics:
  - api_response_time
  - api_success_rate
  - error_count
  - concurrent_users

alerts:
  - high_error_rate
  - slow_response
  - api_quota_exceeded
```

## 📞 技术支持

### 开发团队联系方式
- 📧 技术支持: tech-support@example.com
- 📞 紧急联系: +86-xxx-xxxx-xxxx
- 📖 文档中心: https://docs.example.com

### 社区资源
- 🌟 GitHub: https://github.com/your-org/travel-agent
- 💬 讨论区: https://discussions.example.com
- 📚 教程: https://tutorials.example.com

---

🎉 **祝您使用愉快！智能旅游攻略Agent将为您提供最佳的旅游规划体验！**

