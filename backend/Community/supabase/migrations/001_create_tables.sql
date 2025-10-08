-- 创建 Community 模块所需的数据库表结构

-- MBTI 类型表
CREATE TABLE IF NOT EXISTS mbti_types (
    id SERIAL PRIMARY KEY,
    type_code VARCHAR(4) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT
);

-- 兴趣爱好表
CREATE TABLE IF NOT EXISTS hobbies (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    category VARCHAR(50)
);

-- 旅行目的地表
CREATE TABLE IF NOT EXISTS destinations (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    country VARCHAR(100),
    description TEXT
);

-- 作息习惯表
CREATE TABLE IF NOT EXISTS schedules (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT
);

-- 预算范围表
CREATE TABLE IF NOT EXISTS budgets (
    id SERIAL PRIMARY KEY,
    range_name VARCHAR(100) UNIQUE NOT NULL,
    min_amount INTEGER,
    max_amount INTEGER,
    description TEXT
);

-- 用户表
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    mbti_type_id INTEGER REFERENCES mbti_types(id),
    preferred_destination_id INTEGER REFERENCES destinations(id),
    schedule_id INTEGER REFERENCES schedules(id),
    budget_id INTEGER REFERENCES budgets(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 用户兴趣爱好关联表
CREATE TABLE IF NOT EXISTS user_hobbies (
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    hobby_id INTEGER REFERENCES hobbies(id) ON DELETE CASCADE,
    PRIMARY KEY (user_id, hobby_id)
);

-- 团队表
CREATE TABLE IF NOT EXISTS teams (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    destination_id INTEGER REFERENCES destinations(id),
    max_members INTEGER DEFAULT 6,
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 团队成员关联表
CREATE TABLE IF NOT EXISTS team_members (
    team_id INTEGER REFERENCES teams(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (team_id, user_id)
);

-- 匹配记录表
CREATE TABLE IF NOT EXISTS match_records (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    matched_user_id INTEGER REFERENCES users(id),
    compatibility_score FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 消息表
CREATE TABLE IF NOT EXISTS messages (
    id SERIAL PRIMARY KEY,
    sender_id INTEGER REFERENCES users(id),
    receiver_id INTEGER REFERENCES users(id),
    team_id INTEGER REFERENCES teams(id),
    content TEXT NOT NULL,
    message_type VARCHAR(50) DEFAULT 'text',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 为 anon 和 authenticated 角色授予权限
GRANT SELECT ON ALL TABLES IN SCHEMA public TO anon;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO authenticated;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO authenticated;