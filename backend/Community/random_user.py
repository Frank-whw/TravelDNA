import random
from faker import Faker
from app import db
from app.models import User, Hobby, MbtiType, Destination, Schedule, Budget

# 初始化Faker
fake = Faker('zh_CN')

def generate_random_users(count=20):
    """生成指定数量的随机用户并添加到数据库"""
    # 获取所有可选的字典数据
    mbti_types = MbtiType.query.all()
    hobbies = Hobby.query.all()
    destinations = Destination.query.all()
    schedules = Schedule.query.all()
    budgets = Budget.query.all()
    
    # 检查是否有足够的字典数据
    if not all([mbti_types, hobbies, destinations, schedules, budgets]):
        raise ValueError("请先初始化字典数据，运行/init-data接口")
    
    users = []
    
    for _ in range(count):
        # 随机选择基础信息
        gender = random.choice(["男", "女", "其他"])
        age = random.randint(18, 60)
        mbti = random.choice(mbti_types)
        destination = random.choice(destinations)
        schedule = random.choice(schedules)
        budget = random.choice(budgets)
        
        # 随机选择2-5个兴趣爱好
        selected_hobbies = random.sample(hobbies, random.randint(2, 5))
        
        # 创建用户
        user = User(
            name=fake.name(),
            avatar=f"https://picsum.photos/seed/{fake.uuid4()}/200/200",
            bio=fake.text(max_nb_chars=100),
            gender=gender,
            age=age,
            mbti_id=mbti.id,
            travel_destination_id=destination.id,
            schedule_id=schedule.id,
            budget_id=budget.id
        )
        
        # 添加兴趣爱好
        user.hobbies = selected_hobbies
        
        users.append(user)
    
    try:
        db.session.add_all(users)
        db.session.commit()
        print(f"成功创建{len(users)}个随机用户")
        return users
    except Exception as e:
        db.session.rollback()
        print(f"创建用户失败: {str(e)}")
        return []

# 在应用上下文中运行时使用
if __name__ == "__main__":
    # 这部分代码用于单独运行脚本时初始化应用
    from app import create_app
    app = create_app()
    with app.app_context():
        generate_random_users(20)
