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
## 运行
数据库创建Community数据库，然后可以运行random_user.py进行初始化
在前端app/community/communityApi.ts中配置url  
然后运行，run.py
```shell
python run.py
```