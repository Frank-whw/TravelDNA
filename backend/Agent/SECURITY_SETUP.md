# 🔐 安全配置指南

## ⚠️ 重要安全提醒

**本项目已移除所有硬编码的API密钥，请务必按照以下步骤正确配置环境变量，避免敏感信息泄露！**

## 📋 配置步骤

### 1. 创建环境变量文件

```bash
# 复制示例文件
cp env.example .env
```

### 2. 填入真实API密钥

编辑 `.env` 文件，填入您的真实API密钥：

```bash
# 高德地图API密钥配置
AMAP_WEATHER_API_KEY=您的天气API密钥
AMAP_TRAFFIC_API_KEY=您的交通API密钥  
AMAP_NAVIGATION_API_KEY=您的导航API密钥
AMAP_POI_API_KEY=您的POI搜索API密钥

# 高德地图API安全密钥（如需要）
AMAP_TRAFFIC_SECURITY_KEY=您的交通安全密钥

# 其他配置
DEBUG=false
LOG_LEVEL=INFO
```

### 3. 验证配置

运行以下命令验证配置是否正确：

```bash
python -c "
from config import Config
print('✅ 配置验证:')
print(f'天气API: {'已配置' if Config.AMAP_WEATHER_API_KEY else '❌未配置'}')
print(f'交通API: {'已配置' if Config.AMAP_TRAFFIC_API_KEY else '❌未配置'}')
print(f'导航API: {'已配置' if Config.AMAP_NAVIGATION_API_KEY else '❌未配置'}')
print(f'POI API: {'已配置' if Config.AMAP_POI_API_KEY else '❌未配置'}')
"
```

## 🛡️ 安全最佳实践

### 1. 环境变量保护
- ✅ `.env` 文件已加入 `.gitignore`
- ✅ 绝不提交包含真实API密钥的文件到版本控制
- ✅ 使用 `env.example` 作为配置模板

### 2. API密钥管理
- 🔑 定期轮换API密钥
- 🚫 不在代码中硬编码任何敏感信息
- 📝 为不同环境使用不同的API密钥

### 3. 生产环境部署
```bash
# 生产环境推荐使用系统环境变量
export AMAP_WEATHER_API_KEY=your_production_key
export AMAP_TRAFFIC_API_KEY=your_production_key
# ... 其他密钥
```

### 4. 开发团队协作
- 👥 每个开发者维护自己的 `.env` 文件
- 📋 通过安全渠道共享API密钥（如密码管理器）
- 🔒 禁止在聊天工具中分享API密钥

## 🚨 紧急响应

### 如果API密钥泄露：

1. **立即撤销** 泄露的API密钥
2. **生成新密钥** 并更新配置
3. **检查使用量** 是否有异常调用
4. **更新** 所有相关环境的配置

### 高德地图API密钥管理：

1. 登录 [高德开放平台](https://console.amap.com/)
2. 进入 **应用管理** → **我的应用**
3. 选择对应应用，进入 **管理** 页面
4. 在 **Key列表** 中可以：
   - 查看Key使用情况
   - 重置Key（生成新密钥）
   - 删除不用的Key

## 📊 API使用监控

建议定期检查API使用情况：

```python
# 可以添加API使用量监控
import requests
from datetime import datetime

def check_api_quota():
    """检查API配额使用情况"""
    # 这里可以添加具体的配额检查逻辑
    pass
```

## ✅ 配置检查清单

- [ ] `.env` 文件已创建且不在版本控制中
- [ ] 所有必需的API密钥已配置
- [ ] 配置验证脚本运行成功
- [ ] 团队成员了解安全配置流程
- [ ] 生产环境使用独立的API密钥
- [ ] 设置了API使用量监控

---

🔐 **安全无小事，请严格按照本指南配置！**

