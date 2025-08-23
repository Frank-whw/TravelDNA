# 上海旅游AI助手 (Shanghai Tourism AI Agent)

基于MCP+RAG架构的智能旅游助手，集成实时数据获取与知识库检索，为用户提供全面的上海旅游咨询服务。
（运行方法：直接python api_server.py，然后打开demo。现在的问题是RAG+MCP里的MCP还没做好，这一串功能都用不了。所以目前只能用传统模式。）


## 🏗️ 项目架构

```
Agent/
├── 📁 data/                      # 知识库数据目录
│   ├── 📄 *.txt                 # 文本格式旅游资料  
│   ├── 📄 *.json                # JSON格式旅游数据
│   └── 📄 *.xlsx                # Excel格式数据文件
├── 🐍 Try.py                    # 主程序入口和测试脚本
├── ⚙️ config.py                 # 系统配置文件
├── 🔧 model.py                  # 核心AI模型和助手类
├── 📚 data_loader.py            # 统一数据加载器
├── 🌐 mcp_services.py           # MCP实时服务模块
├── 🔗 mcp_rag_integration.py    # MCP+RAG集成系统
├── 🔍 rag_retrieval.py          # RAG检索引擎
├── 🚀 api_server.py             # Flask API服务器
├── 🎨 demo.html                 # 前端演示页面
├── 📋 requirements.txt          # 项目依赖
└── 📖 README.md                 # 项目说明文档
```

### 核心模块

#### `model.py` - 旅游助手核心
```python
class TourismAssistant:
    """上海旅游AI助手主类"""
    - 支持增强模式（MCP+RAG，目前还没有实现MCP功能）和传统模式（很弱智）切换
    - 集成豆包AI API调用
    - 提供智能问答和路线规划功能
```

#### `mcp_services.py` - 实时服务层
```python
# MCP服务管理器
class MCPServiceManager:
    - WeatherMCPService: 天气信息获取（API缺少）
    - CrowdMCPService: 人流量监控（API缺少）
    - TrafficMCPService: 交通信息查询（API缺少）
```

#### `rag_retrieval.py` - 检索引擎
```python
class HybridRAGRetriever:
    - TraditionalRetriever: 关键词检索
    - VectorRetriever: 向量语义检索
    - 支持按类型搜索(景点/攻略/评价，实现，但是数据不够多)
```

#### `mcp_rag_integration.py` - 集成系统
```python
class MCPRAGIntegrator:
    - 查询意图分析
    - 多源信息融合
    - 智能建议生成
```

### 配置与数据

#### `config.py` - 系统配置
- 🔑 **API配置**：豆包模型、MCP服务端点
- ⚙️ **系统参数**：温度、令牌限制、超时设置
- 🏙️ **上海数据**：景点列表、行政区域划分
- 🔧 **环境配置**：开发/生产/测试环境切换

#### `data_loader.py` - 数据管理
- 📂 **多格式支持**：TXT、JSON、Excel文件加载
- 🔄 **统一接口**：标准化数据加载流程
- 📊 **统计分析**：数据质量和分布统计

## 🚀 快速开始

### ⚡ 5分钟快速部署

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置API密钥
echo "DOUBAO_API_KEY=your_api_key_here" > .env

# 3. 启动API服务器
python api_server.py

# 4. 打开前端演示页面
# 在浏览器中打开 demo.html
```

🎉 **完成！** 访问 http://localhost:5000 查看API状态，或打开演示页面开始体验！

### 📚 更多启动方式

#### 命令行模式
```bash
python Try.py  # 交互式命令行界面
```

#### API模式
```bash
python api_server.py  # 启动REST API服务
```


### 支持的前端技术
- ✅ 原生JavaScript/HTML
- ✅ React.js
- ✅ Vue.js  
- ✅ Angular
- ✅ 微信小程序
- ✅ 移动端H5
