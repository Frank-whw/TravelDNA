# 数据库连接问题排查指南

## 当前问题：DNS 解析失败 `[Errno 11001] getaddrinfo failed`

## 可能的原因分析

### 1. 权限问题（你是 GitHub 成员但不是 Supabase 成员）✅ 这是关键！

**问题：**
- 如果你是 GitHub 项目的成员，但 **不是 Supabase 项目的成员/协作者**
- 你可能：
  - ❌ 无法访问 Supabase Dashboard
  - ❌ 无法获取最新的数据库连接信息
  - ❌ 无法查看数据库设置（IP 白名单、连接池等）
  - ❌ 连接字符串可能已过期或错误

**但要注意：**
- DNS 解析失败本身是网络层面的问题
- 即使有正确的连接字符串，也可能因为网络/DNS 问题无法解析

### 2. 网络/DNS 问题

即使有权限，也可能因为：
- 本地 DNS 服务器无法解析 `db.itqildytorcyteeuejnr.supabase.co`
- 网络防火墙阻止了对 Supabase 的访问
- 使用了 VPN/代理导致 DNS 解析异常

## 解决方案

### 方案1：请求 Supabase 项目访问权限 ⭐ 推荐

**步骤：**

1. **联系项目管理员（Supabase 项目所有者）**
   - 请求添加到 Supabase 项目作为协作者（Collaborator）
   - 或者请求分享数据库连接信息

2. **获取最新的连接信息：**
   - 连接池连接字符串（推荐）
   - 或者直接数据库连接字符串
   - 确认 IP 白名单设置（如果需要）

3. **更新 `.env` 文件**

### 方案2：从项目管理员获取连接信息

如果无法获得 Supabase 访问权限：

1. **请项目管理员提供：**
   - 最新的数据库连接字符串（特别是连接池的）
   - 确认是否需要设置 IP 白名单
   - 项目使用的 Supabase 区域（region）

2. **更新本地 `.env` 文件**

### 方案3：测试网络连接（先排查网络问题）

在获取权限之前，先检查网络是否正常：

#### 3.1 测试 DNS 解析

```powershell
# Windows PowerShell
nslookup db.itqildytorcyteeuejnr.supabase.co

# 或者
Resolve-DnsName db.itqildytorcyteeuejnr.supabase.co
```

#### 3.2 测试网络连通性

```powershell
# 测试是否能访问 Supabase
ping db.itqildytorcyteeuejnr.supabase.co

# 测试 HTTPS（Supabase API）
curl https://itqildytorcyteeuejnr.supabase.co
```

#### 3.3 更换 DNS 服务器（如果 DNS 解析失败）

**临时使用 Google DNS：**
```powershell
# 以管理员身份运行 PowerShell
netsh interface ip set dns "你的网络适配器名称" static 8.8.8.8
netsh interface ip add dns "你的网络适配器名称" 8.8.4.4 index=2
```

### 方案4：使用连接池（如果管理员提供了连接字符串）

连接池通常更容易连接，因为：
- ✅ 不需要 IP 白名单（通常）
- ✅ 使用更通用的域名（pooler.supabase.com）
- ✅ 端口 6543 通常不会被阻止

**连接池格式：**
```
postgresql://postgres.[project-ref]:[password]@aws-0-[region].pooler.supabase.com:6543/postgres
```

## 立即行动步骤

### 步骤 1：联系项目管理员
- [ ] 发送请求：请求 Supabase 项目协作者权限
- [ ] 或请求：最新的数据库连接字符串

### 步骤 2：检查现有连接字符串
- [ ] 确认当前 `.env` 中的连接字符串是否正确
- [ ] 确认是否使用了连接池（端口 6543）还是直接连接（端口 5432）

### 步骤 3：测试网络（可选）
```powershell
# 运行诊断脚本
python test_connection.py

# 或手动测试 DNS
nslookup db.itqildytorcyteeuejnr.supabase.co
```

### 步骤 4：更新连接信息
- [ ] 从管理员处获取正确的连接字符串
- [ ] 运行 `python update_env_connection.py` 更新 `.env`
- [ ] 或手动编辑 `.env` 文件

## 临时解决方案（如果无法获得权限）

如果你暂时无法获得 Supabase 访问权限：

1. **使用本地 SQLite 数据库进行开发**（如果项目支持）
2. **询问管理员是否可以分享只读的数据库连接**（用于测试）
3. **等待获得权限后再连接生产数据库**

## 检查清单

在联系管理员之前，先确认：

- [ ] 你是否是 Supabase 项目的成员/协作者？
- [ ] 你是否有 Supabase Dashboard 的访问权限？
- [ ] 当前的连接字符串是从哪里获得的？
- [ ] 连接字符串是否是最新的？
- [ ] 是否尝试过连接池连接字符串（端口 6543）？

## 需要向管理员询问的信息

如果你需要联系管理员，请询问：

1. **Supabase 项目访问权限**
   - 能否将我添加为协作者？
   - 或者能否分享数据库连接信息？

2. **连接信息**
   - 最新的数据库连接字符串是什么？
   - 应该使用连接池（Connection Pooling）还是直接连接？
   - 是否需要设置 IP 白名单？

3. **网络设置**
   - 数据库是否需要 IP 白名单？
   - 是否有特殊的网络要求？

