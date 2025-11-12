# 知旅（TravelDNA）旅行推荐平台

## 项目概览
知旅是一套面向旅行规划的应用，目标是把“去哪儿玩”“怎么安排”“有什么注意事项”这些问题集中解决。系统会采集天气、人流、交通等信息，再结合用户给出的偏好，为每个人生成贴合实际的行程方案。

## 主要功能
- **行程顾问**：根据问卷和历史偏好，给出更合适的目的地与玩法建议。
- **路线规划**：自动考虑天气、人流、预算等条件，生成可执行的每日安排。
- **旅行社区**：支持组队、聊天、分享出行经验。
- **数据看板**：整合天气、交通、热门程度等信息，帮助临场决策。
- **偏好记忆**：记录并维护用户画像，后续推荐会越来越符合个人习惯。

## Agent 模块在做什么
- **推荐引擎**：负责画像构建、景点筛选、路线编排，把“喜欢什么”与“城市里有什么”对上号。
- **实时数据接入**：调用天气、人流、交通等接口，把最新情况反映到行程里。
- **问答助手**：提供 `/chat` 接口，可与前端会话组件对接，回答行程相关问题。
- **计划调整**：支持对既有行程做调整、优化或追加建议。

## Community 模块的作用
- **用户与权限**：维护基础用户信息、认证逻辑和偏好设置。
- **结伴组队**：提供队伍创建、成员管理、匹配推荐等接口，方便一起出行。
- **实时沟通**：内置消息流接口，队伍成员可以同步计划、交换情报。
- **共享知识**：社区页面集中展示热门路线、评价与游记，为推荐模型提供额外参考。

## 推荐逻辑（简明版）
主要就是把“人”和“地点”都拆成一组标签，然后用相似度判断合不合适：

1. **建画像**：根据旅型、兴趣、预算等打出标签，例如“history=0.8”“indoor=0.3”。
2. **描摹景点**：实时抓取 POI 数据，识别它的类型、价位、人流、天气依赖等，转换成同样的标签格式。
3. **算匹配度**：用余弦相似度测二者的贴合程度，基础分满分 100。
4. **考虑现实情况**：如果那天在下雨、景点太挤或超预算，就扣掉对应的分值。
5. **组装行程**：把得分高的景点按天分配，附上时间推荐、替换方案和注意事项。

一句话总结：先理解用户想法，再对照城市里的选择，最后把天气、人流、预算这些现实限制一起纳入计划中。

## 技术选型

### 前端
- Next.js 15.2.4 + React 18
- Tailwind CSS、shadcn/ui
- Zustand 管理全局状态
- Fetch API 统一请求
- TypeScript + ESLint 保证质量

### 后端
- Community 模块：Flask + SQLAlchemy + SQLite
- Agent 模块：Flask，负责推荐逻辑和实时数据整合
- 数据存储：SQLite（开发环境）
- API 风格：RESTful
- 外部服务：高德地图、天气与交通接口

## 项目结构
```
TravelDNA/
├── frontend/                 # 前端项目
│   ├── app/                 # Next.js App Router
│   │   ├── chat/           # AI聊天页面
│   │   ├── community/      # 社区功能页面
│   │   ├── planning/       # 旅游规划页面
│   │   ├── globals.css     # 全局样式
│   │   ├── layout.tsx      # 全局布局
│   │   └── page.tsx        # 首页
│   ├── components/         # 可复用组件
│   │   ├── ui/            # UI基础组件
│   │   └── ...            # 业务组件
│   ├── lib/               # 工具库和API服务
│   ├── public/            # 静态资源
│   ├── components.json    # shadcn/ui配置
│   ├── next.config.mjs    # Next.js配置
│   ├── package.json       # 前端依赖
│   ├── tailwind.config.ts # Tailwind配置
│   └── tsconfig.json      # TypeScript配置
├── backend/               # 后端项目
│   ├── Community/         # 社区功能模块
│   │   ├── app/          # Flask应用
│   │   ├── models/       # 数据模型
│   │   ├── app.py        # 启动文件
│   │   └── requirements.txt
│   └── Agent/            # AI智能助手模块
│       ├── data/         # 数据文件
│       │   ├── attractions/ # 景点数据
│       │   ├── rag_corpus/  # RAG语料库
│       │   └── reviews/     # 评论数据
│       ├── app.py        # 启动文件
│       ├── config.py     # 配置文件
│       ├── requirements.txt
│       └── travel_agent.py # 核心服务逻辑
├── supabase/             # Supabase配置
├── .env.example          # 环境变量示例
├── .gitignore           # Git忽略文件
├── PROJECT_STRUCTURE.md # 项目结构说明
├── README.md            # 项目说明文档
└── requirements.txt     # 项目依赖
```

## 快速开始

### 环境要求
- Node.js >= 18.0.0
- Python >= 3.8
- npm 或 pnpm

### 安装步骤

1. **克隆项目**
   ```bash
   git clone [本仓库地址]
   cd TravelDNA
   ```

2. **安装后端依赖**
   
   安装Community模块依赖：
   ```bash
   cd backend/Community
   pip install -r requirements.txt
   ```
   
   安装Agent模块依赖：
   ```bash
   cd ../Agent
   pip install -r requirements.txt
   ```

3. **安装前端依赖**
   ```bash
   cd ../../frontend
   npm install
   # 或使用 pnpm
   pnpm install
   ```

4. **环境配置**
   ```bash
   # 复制环境变量示例文件
   cp .env.example .env
   # 根据需要修改 .env 文件中的配置
   ```

### 运行项目

#### 启动后端服务

1. **启动Community模块**（端口：5000）
   ```bash
   cd backend/Community
   python app.py
   ```

2. **启动Agent模块**（端口：5001）
   ```bash
   cd backend/Agent
   python app.py
   ```

#### 启动前端服务
```bash
cd frontend
npm run dev
# 访问 http://localhost:3000
```

### 开发模式

完整的开发环境需要同时运行：
- 前端服务：http://localhost:3000
- Community后端：http://localhost:5000
- Agent后端：http://localhost:5001

## API文档

### Community模块 API

**基础URL**: `http://localhost:5000/api/v1`

#### 系统管理
- `GET /init-data` - 初始化默认数据

#### 用户管理
- `GET /users/{id}` - 获取用户信息
- `POST /users` - 创建用户
- `PUT /users/{id}` - 更新用户信息

#### 队伍管理
- `GET /teams` - 获取队伍列表（需要user_id参数）
- `POST /teams` - 创建队伍
- `DELETE /teams/{id}` - 删除队伍
- `POST /teams/{id}/members` - 添加队伍成员
- `DELETE /teams/{id}/members/{user_id}` - 移除队伍成员

#### 消息系统
- `GET /teams/{id}/messages` - 获取队伍消息（支持lastMsgId增量获取）
- `POST /teams/{id}/messages` - 发送消息

#### 匹配系统
- `GET /users/{id}/matches` - 获取用户匹配记录
- `POST /users/{id}/find-matches` - 查找匹配用户

### Agent模块 API

**基础URL**: `http://localhost:5001/api/v1`

#### 系统状态
- `GET /health` - 健康检查

#### AI聊天
- `POST /chat` - AI智能问答
  ```json
  {
    "message": "用户消息",
    "context": {
      "user_id": "用户ID"
    }
  }
  ```

#### 旅游规划
- `POST /travel-plan` - 创建旅游计划
- `GET /travel/plan/{id}` - 获取计划详情
- `POST /travel/plan/{id}/adjust` - 调整计划
- `POST /travel/plan/{id}/optimize` - 优化路线

#### 信息查询
- `GET /poi/search` - 搜索景点
- `GET /travel/weather` - 获取天气信息
- `GET /travel/traffic` - 获取交通信息
- `GET /travel/crowd` - 获取人流信息

#### 偏好设置
- `GET /travel/preferences/questions` - 获取偏好问题列表

## 开发指南
### 前端开发

1. **组件开发**：使用shadcn/ui组件库，遵循组件化开发原则
2. **状态管理**：使用Zustand进行全局状态管理
3. **API调用**：统一使用lib目录下的API服务文件
4. **样式规范**：使用Tailwind CSS，避免内联样式

### 后端开发

1. **模块化设计**：Community和Agent模块独立开发和部署
2. **API规范**：遵循RESTful API设计原则
3. **错误处理**：统一的错误响应格式
4. **数据验证**：对所有输入数据进行验证

### 代码规范

- 前端代码使用 TypeScript
- 遵循项目内置的 ESLint 规则
- Git 提交信息使用语义化格式
- 关键模块需要配套文档或注释

## 部署说明

### 生产环境部署

1. **前端部署**
   ```bash
   cd frontend
   npm run build
   npm start
   ```

2. **后端部署**
   - 使用WSGI服务器（如Gunicorn）部署Flask应用
   - 配置反向代理（如Nginx）
   - 设置环境变量和配置文件

### 环境变量配置

创建`.env`文件并配置以下变量：
```env
# 前端配置
NEXT_PUBLIC_API_URL=http://localhost:5000/api/v1
NEXT_PUBLIC_AGENT_API_URL=http://localhost:5001/api/v1

# Community后端配置
FLASK_ENV=development
DATABASE_URL=sqlite:///travel.db
SECRET_KEY=your-secret-key

# Agent后端配置
FLASK_HOST=0.0.0.0
FLASK_PORT=5001
FLASK_DEBUG=False

# API密钥配置（Agent模块需要）
AMAP_API_KEY=your-amap-api-key
AMAP_NAVIGATION_KEY=your-navigation-key
AMAP_TRAFFIC_KEY=your-traffic-key
WEATHER_API_KEY=your-weather-api-key
```

## 贡献指南

1. Fork项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建Pull Request

## 许可证
本项目采用MIT许可证 - 查看[LICENSE](LICENSE)文件了解详情

## 联系我们

如有问题或建议，请通过以下方式联系：
- 项目Issues：[GitHub Issues](https://github.com/your-repo/issues)
- 邮箱：your-email@example.com

---

**注意**：本项目仍在积极开发中，功能和API可能会发生变化。建议在生产环境使用前进行充分测试。
