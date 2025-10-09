# 🧠 智能旅游规划Agent系统

基于思考链（Chain of Thought）的先进旅游规划AI系统，具备人文关怀和数据驱动决策能力。

## 🌟 核心特性

### 1. 思考链系统
- ✅ AI深度分析用户需求，生成详细思考过程
- ✅ 透明的决策过程，让用户了解每一步思考
- ✅ 智能API调用策略，只调用必要的服务

### 2. 人文关怀
- ✅ 识别同伴关系（女朋友、父母、朋友等）
- ✅ 理解情感需求（浪漫、温馨、避开人群等）
- ✅ 考虑预算档次，提供个性化推荐
- ✅ 尊重特殊偏好（风土人情、小众景点等）

### 3. 数据驱动
- ✅ 实时天气数据
- ✅ 路况和交通信息
- ✅ POI景点和餐厅数据
- ✅ 智能输入提示（模糊关键词识别）

## 🚀 快速开始

### 1. 安装依赖

```bash
cd TravelAgent
pip install -r requirements.txt
```

### 2. 配置API密钥

复制环境变量示例文件：

```bash
copy .env.example .env  # Windows
cp .env.example .env    # Linux/Mac
```

编辑 `.env` 文件，填入你的API密钥：

```bash
# 豆包API密钥（必需）
DOUBAO_API_KEY=你的豆包API密钥

# 高德地图API密钥（可以使用同一个Web服务API密钥）
AMAP_WEATHER_API_KEY=你的高德API密钥
AMAP_TRAFFIC_API_KEY=你的高德API密钥
AMAP_NAVIGATION_API_KEY=你的高德API密钥
AMAP_POI_API_KEY=你的高德API密钥
AMAP_PROMPT_API_KEY=你的高德API密钥
```

### 3. 运行Agent

#### 方式1：直接运行

```bash
python enhanced_travel_agent.py
```

#### 方式2：Python代码调用

```python
from enhanced_travel_agent import EnhancedTravelAgent

# 初始化Agent
agent = EnhancedTravelAgent()

# 处理用户请求
response = agent.process_user_request(
    "我想带女朋友去上海玩3天，预算2万，想感受风土人情，避开人多的地方",
    show_thoughts=True  # 显示思考过程
)

print(response)
```

#### 方式3：使用快速开始脚本

```bash
python quick_start.py
```

## 📖 详细文档

- [思考链系统说明](./THOUGHT_CHAIN_SYSTEM.md) - 详细的系统架构和工作原理
- [输入提示API说明](./INPUTTIPS_API_README.md) - 输入提示API的使用方法

## 🔑 API密钥获取

### 豆包API
1. 访问 [火山引擎-豆包](https://www.volcengine.com/docs/82379)
2. 注册并创建应用
3. 获取API密钥

### 高德地图API
1. 访问 [高德开放平台](https://lbs.amap.com/)
2. 注册开发者账号
3. 创建应用，选择 **Web服务API** 类型
4. 获取API密钥（Key）
5. 同一个密钥可用于天气、导航、POI、交通等所有服务

## 💡 使用示例

### 示例1：情侣浪漫之旅
```python
response = agent.process_user_request(
    "我想带女朋友去上海玩3天，预算2万，想要浪漫氛围"
)
```

**系统识别到**：
- 👥 同伴：女朋友（浪漫之旅）
- 💰 预算：20000元（高端档次）
- 💝 情感需求：浪漫氛围

**推荐风格**：浪漫景点、高端餐厅、情侣适合的活动

### 示例2：家庭亲子游
```python
response = agent.process_user_request(
    "带父母和孩子去上海玩5天，要轻松舒适"
)
```

**系统识别到**：
- 👥 同伴：父母、孩子（家庭出游）
- 💝 情感需求：轻松舒适

**推荐风格**：便捷交通、全家适合、舒适安排

### 示例3：深度文化游
```python
response = agent.process_user_request(
    "想了解上海的风土人情，避开热门景点，深度游7天"
)
```

**系统识别到**：
- ⭐ 特殊偏好：风土人情、小众景点、深度游
- 💝 情感需求：避开人群

**推荐风格**：小众景点、当地特色、文化体验

## 🎯 系统工作流程

```
用户输入
    ↓
📋 Step 1: AI深度理解需求，生成思考链
    ├─ 识别同伴关系（女朋友、父母等）
    ├─ 提取情感需求（浪漫、温馨等）
    ├─ 分析预算档次
    └─ 理解特殊偏好
    ↓
🔍 Step 2: 提取关键信息
    ├─ 使用AI总结完整意图（保留人文细节）
    ├─ 使用输入提示API识别模糊地点
    └─ 提取所有人文因素
    ↓
🤖 Step 3: 智能决定需要的API
    ├─ 根据思考链选择API
    ├─ 优化调用策略
    └─ 避免不必要的请求
    ↓
📡 Step 4: 收集实时数据
    ├─ 天气API（多日天气）
    ├─ POI API（景点和餐厅）
    ├─ 导航API（路线规划）
    ├─ 路况API（实时交通）
    └─ 输入提示API（地点识别）
    ↓
💡 Step 5: 生成个性化攻略
    ├─ 根据同伴关系调整风格
    ├─ 根据情感需求选择景点
    ├─ 根据预算推荐消费场所
    └─ 提供温暖、人性化的建议
```

## 📦 依赖说明

```
requests>=2.31.0       # HTTP请求
python-dotenv>=1.0.0   # 环境变量管理
pandas>=2.0.0          # 数据处理（可选）
urllib3>=2.0.0         # HTTP库
```

## 🔧 配置说明

### config.py 主要配置项

- `DOUBAO_API_KEY`: 豆包AI的API密钥
- `AMAP_*_API_KEY`: 高德地图各服务的API密钥
- `FLASK_ENV`: 运行环境（development/production/testing）

## 🧪 测试

### 测试输入提示API
```bash
python test_inputtips.py
```

### 测试完整系统
```bash
python enhanced_travel_agent.py
```

## ⚠️ 注意事项

1. **API调用限制**
   - 遵守各API的调用频率限制
   - 系统已优化，只调用必要的API

2. **数据准确性**
   - 天气数据：实时获取，准确度高
   - 路况数据：实时更新
   - POI数据：基于高德地图数据库

3. **隐私保护**
   - 不上传用户个人信息
   - API密钥请妥善保管

## 📝 更新日志

- **v1.0.0** (2025-10-08)
  - ✅ 实现思考链系统
  - ✅ 添加人文因素识别
  - ✅ 集成输入提示API
  - ✅ 优化API调用策略
  - ✅ 完善文档和示例

## 📧 联系方式

- 问题反馈：[GitHub Issues]
- 文档：查看 `THOUGHT_CHAIN_SYSTEM.md`

## 📄 许可证

MIT License

---

**版本**: 1.0.0  
**最后更新**: 2025-10-08

