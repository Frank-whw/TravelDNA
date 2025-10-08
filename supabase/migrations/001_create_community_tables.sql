-- Community 模块数据库表结构迁移
-- 创建用户、队伍、匹配记录和消息相关表

-- 用户表
CREATE TABLE IF NOT EXISTS "user" (
    id SERIAL PRIMARY KEY,
    username VARCHAR(80) UNIQUE NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    nickname VARCHAR(50),
    avatar_url VARCHAR(255),
    bio TEXT,
    age INTEGER,
    gender VARCHAR(10),
    location VARCHAR(100),
    interests TEXT,
    travel_style VARCHAR(50),
    budget_range VARCHAR(50),
    preferred_destinations TEXT,
    languages TEXT,
    contact_info VARCHAR(255),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 队伍表
CREATE TABLE IF NOT EXISTS team (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    destination VARCHAR(100) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    max_members INTEGER DEFAULT 6,
    current_members INTEGER DEFAULT 1,
    budget_per_person DECIMAL(10,2),
    travel_style VARCHAR(50),
    requirements TEXT,
    status VARCHAR(20) DEFAULT 'recruiting',
    creator_id INTEGER NOT NULL REFERENCES "user"(id) ON DELETE CASCADE,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 队伍成员表
CREATE TABLE IF NOT EXISTS team_member (
    id SERIAL PRIMARY KEY,
    team_id INTEGER NOT NULL REFERENCES team(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES "user"(id) ON DELETE CASCADE,
    role VARCHAR(20) DEFAULT 'member',
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) DEFAULT 'active',
    UNIQUE(team_id, user_id)
);

-- 匹配记录表
CREATE TABLE IF NOT EXISTS match_record (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES "user"(id) ON DELETE CASCADE,
    matched_user_id INTEGER NOT NULL REFERENCES "user"(id) ON DELETE CASCADE,
    compatibility_score DECIMAL(5,2) NOT NULL,
    match_reasons TEXT,
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 消息表
CREATE TABLE IF NOT EXISTS message (
    id SERIAL PRIMARY KEY,
    team_id INTEGER NOT NULL REFERENCES team(id) ON DELETE CASCADE,
    sender_id INTEGER NOT NULL REFERENCES "user"(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    message_type VARCHAR(20) DEFAULT 'text',
    is_read BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建索引以提高查询性能
CREATE INDEX IF NOT EXISTS idx_user_username ON "user"(username);
CREATE INDEX IF NOT EXISTS idx_user_email ON "user"(email);
CREATE INDEX IF NOT EXISTS idx_team_creator ON team(creator_id);
CREATE INDEX IF NOT EXISTS idx_team_destination ON team(destination);
CREATE INDEX IF NOT EXISTS idx_team_status ON team(status);
CREATE INDEX IF NOT EXISTS idx_team_member_team ON team_member(team_id);
CREATE INDEX IF NOT EXISTS idx_team_member_user ON team_member(user_id);
CREATE INDEX IF NOT EXISTS idx_match_record_user ON match_record(user_id);
CREATE INDEX IF NOT EXISTS idx_match_record_matched_user ON match_record(matched_user_id);
CREATE INDEX IF NOT EXISTS idx_message_team ON message(team_id);
CREATE INDEX IF NOT EXISTS idx_message_sender ON message(sender_id);

-- 创建更新时间触发器函数
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 为需要的表创建更新时间触发器
CREATE TRIGGER update_user_updated_at BEFORE UPDATE ON "user"
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_team_updated_at BEFORE UPDATE ON team
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_match_record_updated_at BEFORE UPDATE ON match_record
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- 插入一些示例数据
INSERT INTO "user" (username, email, password_hash, nickname, age, gender, location, interests, travel_style, budget_range) VALUES
('alice_travel', 'alice@example.com', 'hashed_password_1', '爱丽丝', 25, 'female', '北京', '摄影,美食,历史', 'cultural', '3000-5000'),
('bob_adventure', 'bob@example.com', 'hashed_password_2', '鲍勃', 28, 'male', '上海', '户外,冒险,运动', 'adventure', '5000-8000'),
('charlie_budget', 'charlie@example.com', 'hashed_password_3', '查理', 22, 'male', '广州', '背包旅行,青旅', 'budget', '1000-3000')
ON CONFLICT (username) DO NOTHING;

-- 插入示例队伍数据
INSERT INTO team (name, description, destination, start_date, end_date, max_members, budget_per_person, travel_style, creator_id) VALUES
('日本樱花之旅', '春季赏樱，体验日本文化', '日本东京', '2024-04-01', '2024-04-07', 4, 6000.00, 'cultural', 1),
('泰国海岛冒险', '潜水、海滩、夜市美食', '泰国普吉岛', '2024-03-15', '2024-03-22', 6, 4000.00, 'adventure', 2)
ON CONFLICT DO NOTHING;

-- 插入队伍成员数据
INSERT INTO team_member (team_id, user_id, role) VALUES
(1, 1, 'leader'),
(2, 2, 'leader'),
(1, 3, 'member')
ON CONFLICT (team_id, user_id) DO NOTHING;