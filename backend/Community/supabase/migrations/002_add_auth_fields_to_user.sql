-- 添加用户认证相关字段到 user 表
-- 此迁移脚本用于为现有的 user 表添加注册登录所需字段

-- 添加 email 字段（唯一索引）
ALTER TABLE "user" 
ADD COLUMN IF NOT EXISTS email VARCHAR(255);

-- 添加 phone 字段（唯一索引）
ALTER TABLE "user" 
ADD COLUMN IF NOT EXISTS phone VARCHAR(20);

-- 添加 password_hash 字段
ALTER TABLE "user" 
ADD COLUMN IF NOT EXISTS password_hash VARCHAR(255);

-- 添加 salt 字段
ALTER TABLE "user" 
ADD COLUMN IF NOT EXISTS salt VARCHAR(32);

-- 添加 status 字段，默认值为 'active'
ALTER TABLE "user" 
ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'active' NOT NULL;

-- 为 email 创建唯一索引（允许 NULL）
CREATE UNIQUE INDEX IF NOT EXISTS idx_user_email_unique ON "user"(email) WHERE email IS NOT NULL;

-- 为 phone 创建唯一索引（允许 NULL）
CREATE UNIQUE INDEX IF NOT EXISTS idx_user_phone_unique ON "user"(phone) WHERE phone IS NOT NULL;

-- 添加检查约束：email 和 phone 至少有一个不为 NULL
ALTER TABLE "user"
DROP CONSTRAINT IF EXISTS check_email_or_phone;

ALTER TABLE "user"
ADD CONSTRAINT check_email_or_phone 
CHECK ((email IS NOT NULL) OR (phone IS NOT NULL));

-- 为已有用户设置默认状态（如果状态为 NULL）
UPDATE "user" 
SET status = 'active' 
WHERE status IS NULL;

