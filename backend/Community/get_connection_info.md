# Supabase 数据库连接指南

## 问题
DNS 解析失败 `[Errno 11001] getaddrinfo failed`

## 解决方案

### 方案1：使用 Supabase 连接池（推荐）⭐

Supabase 推荐使用连接池而不是直接数据库连接，连接池不需要 IP 白名单，更容易连接。

**步骤：**

1. 登录 [Supabase Dashboard](https://supabase.com/dashboard)
2. 选择你的项目
3. 进入 **Settings** → **Database**
4. 找到 **Connection Pooling** 部分
5. 复制 **Connection string**（应该是类似这样的格式）：
   ```
   postgresql://postgres.[project-ref]:[password]@aws-0-[region].pooler.supabase.com:6543/postgres
   ```
   或
   ```
   postgresql://postgres.[project-ref]:[password]@[region].pooler.supabase.com:6543/postgres
   ```

6. 更新 `.env` 文件中的 `DATABASE_URL`：
   ```
   DATABASE_URL=postgresql://postgres.[project-ref]:23011279Ecust%23@[region].pooler.supabase.com:6543/postgres
   ```

### 方案2：使用 Session Mode（更稳定的连接池）

1. 在 **Connection Pooling** 中找到 **Session mode** 的连接字符串
2. 使用 Session mode 的连接字符串更新 `.env`

### 方案3：检查直接连接（如果必须使用 5432 端口）

如果必须使用直接数据库连接：

1. 进入 **Settings** → **Database** → **Network Restrictions**
2. 添加你的 IP 地址到白名单
   - 或者暂时允许所有 IP（仅用于测试）
3. 确认使用的是正确的直接连接 URL（在 Database → Connection String 中）

### 方案4：检查网络环境

如果以上都不行，可能是网络问题：

1. **检查网络连接**：确保能访问 internet
2. **检查 DNS**：尝试使用其他 DNS 服务器（如 8.8.8.8）
3. **检查代理/防火墙**：如果使用 VPN 或代理，尝试关闭后重试
4. **使用手机热点**：排除公司/学校网络限制

## 获取正确的连接字符串

### 在 Supabase Dashboard 中：

1. **Settings** → **Database** → **Connection String**
   - 选择 **URI** 格式
   - 复制完整的连接字符串

2. **Settings** → **Database** → **Connection Pooling**
   - 复制 **Connection string** 或 **Session mode** 连接字符串

### 连接字符串格式示例：

**直接连接（需要 IP 白名单）：**
```
postgresql://postgres:password@db.xxx.supabase.co:5432/postgres
```

**连接池（推荐，不需要 IP 白名单）：**
```
postgresql://postgres.xxx:password@aws-0-xxx.pooler.supabase.com:6543/postgres
```

## 更新 .env 文件

找到正确的连接字符串后，更新 `.env` 文件：

```
DATABASE_URL=postgresql://postgres.[ref]:23011279Ecust%23@[host]:[port]/postgres
SQLALCHEMY_TRACK_MODIFICATIONS=False
SECRET_KEY=dev-secret-key-change-in-production
```

**注意：** 密码中的特殊字符需要进行 URL 编码：
- `#` → `%23`
- `@` → `%40`
- `&` → `%26`
- 等等

