from app import db
from app.models import User, Hobby, MatchRecord

def calculate_match_score(user1, user2):
    """
    计算两个用户之间的匹配度
    
    匹配规则:
    - MBTI类型相同: 20分
    - 旅行目的地相同: 20分
    - 作息习惯相同: 15分
    - 预算范围相同: 15分
    - 共同兴趣数量: 最多30分(每个共同兴趣10分)
    """
    score = 0
    
    # MBTI类型匹配
    if user1.mbti_id and user2.mbti_id and user1.mbti_id == user2.mbti_id:
        score += 20
    
    # 旅行目的地匹配
    if user1.travel_destination_id and user2.travel_destination_id and user1.travel_destination_id == user2.travel_destination_id:
        score += 20
    
    # 作息习惯匹配
    if user1.schedule_id and user2.schedule_id and user1.schedule_id == user2.schedule_id:
        score += 15
    
    # 预算范围匹配
    if user1.budget_id and user2.budget_id and user1.budget_id == user2.budget_id:
        score += 15
    
    # 共同兴趣匹配
    user1_hobbies = set(h.id for h in user1.hobbies.all())
    user2_hobbies = set(h.id for h in user2.hobbies.all())
    common_hobbies = user1_hobbies.intersection(user2_hobbies)
    score += min(len(common_hobbies) * 10, 30)  # 最多30分
    
    return score

def find_matches(user_id, limit=8):
    """为指定用户寻找匹配的旅行搭子"""
    user = User.query.get(user_id)
    if not user:
        return []
    
    # 获取所有其他用户
    other_users = User.query.filter(User.id != user_id).all()
    
    matches = []
    for other_user in other_users:
        # 计算匹配度
        score = calculate_match_score(user, other_user)
        
        # 只考虑匹配度70分以上的
        if score >= 0:
            # 检查是否已有匹配记录
            existing_match = MatchRecord.query.filter_by(
                user_id=user_id,
                matched_user_id=other_user.id
            ).first()
            
            if existing_match:
                # 更新现有匹配记录
                existing_match.matching_score = score
                existing_match.is_valid = True
                db.session.commit()
                matches.append(existing_match)
            else:
                # 创建新的匹配记录
                new_match = MatchRecord(
                    user_id=user_id,
                    matched_user_id=other_user.id,
                    matching_score=score
                )
                db.session.add(new_match)
                db.session.commit()
                matches.append(new_match)
    
    # 按匹配度排序并返回前limit个结果
    matches.sort(key=lambda x: x.matching_score, reverse=True)
    return matches[:limit]

def init_default_data():
    """初始化默认数据（MBTI类型、兴趣爱好等）"""
    from app.models import MbtiType, Hobby, Destination, Schedule, Budget
    
    # 初始化MBTI类型
    mbti_types = [
        "ISTJ", "ISFJ", "INFJ", "INTJ",
        "ISTP", "ISFP", "INFP", "INTP",
        "ESTP", "ESFP", "ENFP", "ENTP",
        "ESTJ", "ESFJ", "ENFJ", "ENTJ"
    ]
    
    for mbti in mbti_types:
        if not MbtiType.query.filter_by(name=mbti).first():
            db.session.add(MbtiType(name=mbti))
    
    # 初始化兴趣爱好
    hobbies = [
        "美食", "摄影", "徒步", "文化", "购物", 
        "自然风光", "历史古迹", "城市观光", "户外探险",
        "博物馆", "艺术展览", "音乐", "夜生活", "美食探索"
    ]
    
    for hobby in hobbies:
        if not Hobby.query.filter_by(name=hobby).first():
            db.session.add(Hobby(name=hobby))
    
    # 初始化旅行目的地
    destinations = [
        "北京", "上海", "广州", "成都", "杭州", "西安", 
        "三亚", "青岛", "厦门", "重庆", "拉萨", "乌鲁木齐",
        "南京", "苏州", "桂林", "张家界", "九寨沟", "丽江"
    ]
    
    for dest in destinations:
        if not Destination.query.filter_by(name=dest).first():
            db.session.add(Destination(name=dest))
    
    # 初始化作息习惯
    schedules = [
        "早睡早起", "晚睡晚起", "弹性作息", "跟随行程安排"
    ]
    
    for schedule in schedules:
        if not Schedule.query.filter_by(name=schedule).first():
            db.session.add(Schedule(name=schedule))
    
    # 初始化预算范围
    budgets = [
        "经济型", "舒适型", "轻奢型", "豪华型"
    ]
    
    for budget in budgets:
        if not Budget.query.filter_by(name=budget).first():
            db.session.add(Budget(name=budget))
    
    db.session.commit()
