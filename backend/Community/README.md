# 社区后端
## 结构
Community/
├── app/
│ &ensp;&ensp;  ├── __init__.py           # 应用初始化
│ &ensp;&ensp;  ├── config.py             # 配置文件
│ &ensp;&ensp; ├── models.py             # 所有ORM模型
│ &ensp;&ensp;  ├── routes.py             # 所有API路由
│ &ensp;&ensp;  └── utils.py              # 工具函数（匹配算法等）
├── .env                      # 环境变量
└── run.py                    # 启动入口
## 数据库
User表，Team表，Message表，Hobbies表
User与Team是多对多的关系
Team与Message是一对多的关系