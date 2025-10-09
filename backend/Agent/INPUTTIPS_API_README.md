# 高德地图输入提示API使用说明

## 📋 功能简介

输入提示API是一个智能搜索建议服务，类似于搜索框的自动补全功能。当用户输入关键词时，API会返回相关的建议列表，包括POI、公交站、地铁站等信息。

## 🔑 API配置

### 1. 获取API密钥

在高德开放平台（https://lbs.amap.com/）申请 **Web服务API** 类型的密钥。

### 2. 配置环境变量

在 `.env` 文件中添加：

```bash
AMAP_PROMPT_API_KEY=你的高德Web服务API密钥
```

**注意**：输入提示API可以和路径规划、POI搜索等共用同一个Web服务API密钥。

## 📚 使用方法

### 基本用法

```python
from enhanced_travel_agent import EnhancedTravelAgent

# 初始化Agent
agent = EnhancedTravelAgent()

# 搜索景点提示
tips = agent.get_inputtips("外滩", city="上海")

# 打印结果
for tip in tips:
    print(f"名称: {tip['name']}")
    print(f"地址: {tip['address']}")
    print(f"区域: {tip['district']}")
    print(f"坐标: {tip['location']}")
    print()
```

### 高级用法

#### 1. 按POI类型搜索

```python
# 搜索快餐店
tips = agent.get_inputtips(
    "肯德基",
    city="上海",
    poi_type="050301",  # 050301是快餐店的类型代码
    citylimit=True      # 只返回上海的结果
)
```

#### 2. 基于位置的搜索

```python
# 搜索陆家嘴附近的咖啡店
tips = agent.get_inputtips(
    "咖啡",
    city="上海",
    location="121.506377,31.245105",  # 陆家嘴坐标
    citylimit=True
)
```

#### 3. 指定返回数据类型

```python
# 只返回POI数据
tips = agent.get_inputtips(
    "人民广场",
    city="上海",
    datatype="poi"  # 可选: all, poi, bus, busline
)
```

## 📖 参数说明

### `get_inputtips()` 方法参数

| 参数 | 类型 | 必填 | 说明 | 默认值 |
|------|------|------|------|--------|
| `keywords` | str | 是 | 查询关键词 | - |
| `city` | str | 否 | 搜索城市（citycode或城市名） | "上海" |
| `poi_type` | str | 否 | POI分类代码，多个用"\|"分隔 | None |
| `location` | str | 否 | 坐标"经度,纬度"，优先返回附近结果 | None |
| `citylimit` | bool | 否 | 是否仅返回指定城市数据 | False |
| `datatype` | str | 否 | 返回数据类型：all/poi/bus/busline | "all" |

### 返回数据结构

```python
[
    {
        "id": "B000A8UVVV",           # POI ID
        "name": "外滩",                # 名称
        "district": "上海市黄浦区",     # 所属区域
        "adcode": "310101",           # 区域编码
        "location": "121.484,31.240", # 坐标
        "address": "中山东一路",       # 地址
        "typecode": "110000"          # 类型代码
    },
    ...
]
```

## 🎯 常用POI类型代码

| 类型 | 代码 | 说明 |
|------|------|------|
| 餐饮服务 | 050000 | 所有餐饮 |
| 中餐厅 | 050100 | 中餐 |
| 快餐店 | 050300 | 快餐 |
| 咖啡厅 | 050500 | 咖啡 |
| 购物中心 | 060400 | 商场 |
| 风景名胜 | 110000 | 景点 |
| 公园 | 110101 | 公园 |
| 地铁站 | 150500 | 地铁 |
| 公交站 | 150700 | 公交 |

完整的POI类型代码请参考高德官方文档。

## 🧪 测试示例

运行测试脚本：

```bash
cd Agent
python test_inputtips.py
```

测试脚本会演示以下场景：
1. 搜索景点（外滩）
2. 搜索餐厅（肯德基）
3. 搜索商圈（陆家嘉）
4. 搜索地铁站（人民广场）
5. 基于位置的搜索（陆家嘴附近的咖啡）

## 💡 使用场景

1. **智能搜索框**：为用户提供输入建议
2. **地点推荐**：根据关键词推荐相关地点
3. **附近搜索**：基于用户位置推荐周边POI
4. **类型筛选**：按特定类型（餐厅、景点等）筛选建议

## ⚠️ 注意事项

1. **调用限制**：遵守高德API的调用频率限制
2. **坐标格式**：经纬度格式为"经度,纬度"，小数点后不超过6位
3. **城市参数**：建议使用citycode（如上海：310000）
4. **密钥权限**：确保API密钥有输入提示服务的权限

## 🔗 相关文档

- [高德开放平台](https://lbs.amap.com/)
- [输入提示API文档](https://lbs.amap.com/api/webservice/guide/api/inputtips)
- [POI分类编码](https://lbs.amap.com/api/webservice/download)

## 📝 更新日志

- **2025-10-08**: 新增输入提示API支持

