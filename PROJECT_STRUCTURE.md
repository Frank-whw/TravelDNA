# TravelDNA 项目结构说明

## 📁 项目目录结构

```
TravelDNA/
├── .gitignore                    # Git忽略规则（统一管理）
├── .env.example                  # 环境变量配置示例
├── README.md                     # 项目主文档
├── PROJECT_STRUCTURE.md          # 项目结构说明（本文件）
├── AMap_adcode_citycode.xlsx     # 高德地图城市代码映射文件
├── enhanced_travel_agent.py      # 主程序入口（增强版智能旅行Agent）
│
├── .trae/                        # Trae IDE配置目录
│   └── documents/
│
├── api/                          # API路由目录
│   └── routes/
│
├── backend/                      # 后端代码目录
│   ├── .env                      # 后端环境变量（包含敏感信息，已被Git忽略）
│   ├── __init__.py
│   └── Agent/                    # 智能Agent核心代码
│       ├── .gitignore            # Agent模块Git忽略规则
│       ├── README.md             # Agent模块文档
│       ├── config.py             # 系统配置文件（安全版本，使用环境变量）
│       ├── enhanced_travel_agent.py  # 增强版旅行Agent实现
│       ├── mcp_services.py       # MCP服务集成
│       ├── traffic_service.py    # 交通服务模块
│       ├── travel_agent.py       # 基础旅行Agent
│       ├── model.py              # 数据模型定义
│       ├── data/                 # 数据文件目录
│       └── test_*.py             # 测试文件
│
└── frontend/                     # 前端代码目录
    ├── app/                      # Next.js应用目录
    ├── components/               # React组件
    ├── hooks/                    # React Hooks
    ├── lib/                      # 工具库
    ├── public/                   # 静态资源
    ├── styles/                   # 样式文件
    ├── components.json           # 组件配置
    ├── next.config.mjs           # Next.js配置
    ├── package.json              # 前端依赖管理
    ├── package-lock.json         # 依赖锁定文件
    ├── pnpm-lock.yaml            # PNPM锁定文件
    ├── postcss.config.mjs        # PostCSS配置
    ├── tailwind.config.ts        # Tailwind CSS配置
    └── tsconfig.json             # TypeScript配置
```

## 🔧 配置文件说明

### 环境变量配置

1. **`.env.example`** - 环境变量配置示例
   - 包含所有必需和可选的环境变量
   - 复制为 `.env` 文件并填入真实API密钥

2. **`backend/.env`** - 后端环境变量（已存在）
   - 包含心知天气API配置
   - 已被Git忽略，不会提交到版本控制

3. **`backend/Agent/config.py`** - 系统配置文件
   - 使用环境变量读取API密钥（安全）
   - 包含完整的系统配置参数
   - 支持开发、生产、测试环境配置

### Git忽略规则

- **根目录 `.gitignore`** - 统一的Git忽略规则
  - Python相关文件（__pycache__、*.pyc等）
  - Node.js相关文件（node_modules、*.log等）
  - IDE配置文件（.vscode、.idea等）
  - 系统文件（.DS_Store、Thumbs.db等）
  - 敏感文件（.env*、*.key、*.pem等）
  - 缓存和临时文件

## 🚀 快速开始

### 1. 环境配置

```bash
# 复制环境变量配置
cp .env.example .env

# 编辑 .env 文件，填入真实的API密钥
# 至少需要配置 DOUBAO_API_KEY
```

### 2. 运行主程序

```bash
# 运行增强版智能旅行Agent
python enhanced_travel_agent.py
```

### 3. 前端开发

```bash
cd frontend
npm install
npm run dev
```

## 📋 必需的API密钥

### 必需配置
- `DOUBAO_API_KEY` - 豆包AI API密钥（必需）

### 可选配置（按需启用功能）
- `AMAP_WEATHER_API_KEY` - 高德地图天气API
- `AMAP_TRAFFIC_API_KEY` - 高德地图交通API
- `AMAP_NAVIGATION_API_KEY` - 高德地图导航API
- `AMAP_POI_API_KEY` - 高德地图POI搜索API

## 🔒 安全注意事项

1. **API密钥安全**
   - 所有API密钥通过环境变量配置
   - `.env` 文件已被Git忽略
   - 不要在代码中硬编码API密钥

2. **敏感文件**
   - `backend/.env` 包含心知天气API配置
   - 所有 `.env*` 文件（除 `.env.example`）都被Git忽略

3. **缓存文件**
   - `__pycache__` 目录已被清理和忽略
   - 所有编译文件和缓存文件都被Git忽略

## 📝 开发建议

1. **配置管理**
   - 使用 `backend/Agent/config.py` 进行系统配置
   - 通过环境变量管理敏感信息
   - 不同环境使用不同的配置类

2. **代码组织**
   - 后端核心逻辑在 `backend/Agent/` 目录
   - 前端代码在 `frontend/` 目录
   - 主程序入口为 `enhanced_travel_agent.py`

3. **版本控制**
   - 提交前检查 `.gitignore` 规则
   - 不要提交包含API密钥的文件
   - 定期清理缓存和临时文件

## 🔄 文件整理记录

### 已删除的重复/不安全文件
- `config.py`（根目录，包含硬编码API密钥）
- `frontend/.gitignore`（重复的Git忽略规则）
- `__pycache__/`（Python缓存目录）
- `backend/__pycache__/`（Python缓存目录）

### 新增的文件
- `.gitignore`（根目录，统一的Git忽略规则）
- `.env.example`（环境变量配置示例）
- `PROJECT_STRUCTURE.md`（本文件）

### 保留的重要文件
- `backend/Agent/config.py`（安全的配置文件）
- `backend/.env`（现有的环境变量文件）
- `enhanced_travel_agent.py`（主程序入口）