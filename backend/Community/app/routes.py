from flask import Blueprint, request, jsonify
from app import db
from app.models import (
    User, Team, MatchRecord, Message, 
    Hobby, MbtiType, Destination, Schedule, Budget,
    user_hobby,team_member
)
from app.utils import (
    find_matches, init_default_data,
    hash_password, verify_password, generate_salt,
    validate_email, validate_phone
)

# 初始化蓝图
api_bp = Blueprint('api', __name__)

# 初始化默认数据
@api_bp.route('/init-data', methods=['GET', 'POST'])
def initialize_data():
    try:
        init_default_data()
        return jsonify({"status": "success", "message": "默认数据初始化成功"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500


@api_bp.route('/init-users', methods=['POST'])
def init_users():
    from random_user import seed_mock_data

    payload = request.get_json(silent=True) or {}
    try:
        stats = seed_mock_data(
            users=int(payload.get("users") or payload.get("count") or 200),
            teams=int(payload.get("teams") or 60),
            min_members=int(payload.get("minMembers") or payload.get("min_members") or 3),
            max_members=int(payload.get("maxMembers") or payload.get("max_members") or 8),
            messages_per_team=int(payload.get("messagesPerTeam") or payload.get("messages_per_team") or 25),
            matches_per_user=int(payload.get("matchesPerUser") or payload.get("matches_per_user") or 10),
            min_match_score=int(payload.get("minMatchScore") or payload.get("min_match_score") or 60),
            purge=bool(payload.get("purge", False)),
        )
        # 将 top_cities 列表转换为可序列化格式
        if "top_cities" in stats:
            stats["top_cities"] = [
                {"city": city, "count": count} for city, count in stats["top_cities"]
            ]
        return jsonify({"status": "success", "message": "测试用户生成完成", "data": stats})
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500

# 认证相关接口
@api_bp.route('/auth/register', methods=['POST'])
def register():
    """用户注册"""
    data = request.get_json()
    
    if not data:
        return jsonify({"status": "error", "message": "请求数据不能为空"}), 400
    
    # 验证必填字段
    email = data.get('email', '').strip()
    phone = data.get('phone', '').strip()
    password = data.get('password', '').strip()
    name = data.get('name', '').strip()
    gender = data.get('gender', '').strip()
    age = data.get('age')
    
    # email 和 phone 至少有一个
    if not email and not phone:
        return jsonify({"status": "error", "message": "邮箱或手机号至少填写一个"}), 400
    
    # 验证格式
    if email and not validate_email(email):
        return jsonify({"status": "error", "message": "邮箱格式不正确"}), 400
    
    if phone and not validate_phone(phone):
        return jsonify({"status": "error", "message": "手机号格式不正确"}), 400
    
    # 验证密码
    if not password or len(password) < 6:
        return jsonify({"status": "error", "message": "密码长度至少为6位"}), 400
    
    # 验证基本信息
    if not name:
        return jsonify({"status": "error", "message": "昵称不能为空"}), 400
    
    if not gender:
        return jsonify({"status": "error", "message": "性别不能为空"}), 400
    
    if not age or not isinstance(age, int) or age < 1 or age > 150:
        return jsonify({"status": "error", "message": "年龄必须为1-150之间的整数"}), 400
    
    # 检查邮箱或手机号是否已存在
    existing_user = None
    if email:
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            return jsonify({"status": "error", "message": "该邮箱已被注册"}), 400
    
    if phone:
        existing_user = User.query.filter_by(phone=phone).first()
        if existing_user:
            return jsonify({"status": "error", "message": "该手机号已被注册"}), 400
    
    try:
        # 生成密码哈希和盐值
        password_hash, salt = hash_password(password)
        
        # 创建用户
        user = User(
            email=email if email else None,
            phone=phone if phone else None,
            password_hash=password_hash,
            salt=salt,
            name=name,
            gender=gender,
            age=age,
            status='active',
            bio=data.get('bio', ''),
            avatar=data.get('avatar', '')
        )
        
        db.session.add(user)
        db.session.commit()
        
        return jsonify({
            "status": "success",
            "message": "注册成功",
            "data": user.to_dict()
        }), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": f"注册失败: {str(e)}"}), 500

@api_bp.route('/auth/login', methods=['POST'])
def login():
    """用户登录"""
    data = request.get_json()
    
    if not data:
        return jsonify({"status": "error", "message": "请求数据不能为空"}), 400
    
    # 支持邮箱或手机号登录
    account = data.get('account', '').strip()  # 可以是邮箱或手机号
    password = data.get('password', '').strip()
    
    if not account or not password:
        return jsonify({"status": "error", "message": "账号和密码不能为空"}), 400
    
    # 查找用户
    user = None
    if validate_email(account):
        user = User.query.filter_by(email=account).first()
    elif validate_phone(account):
        user = User.query.filter_by(phone=account).first()
    else:
        return jsonify({"status": "error", "message": "账号格式不正确，请输入邮箱或手机号"}), 400
    
    if not user:
        return jsonify({"status": "error", "message": "账号或密码错误"}), 401
    
    # 验证密码
    if not user.password_hash or not user.salt:
        return jsonify({"status": "error", "message": "账号未设置密码，请联系管理员"}), 401
    
    if not verify_password(password, user.password_hash, user.salt):
        return jsonify({"status": "error", "message": "账号或密码错误"}), 401
    
    # 检查账号状态
    if user.status != 'active':
        return jsonify({"status": "error", "message": f"账号已被{user.status}"}), 403
    
    # 登录成功，返回用户信息（不包含敏感信息）
    return jsonify({
        "status": "success",
        "message": "登录成功",
        "data": user.to_dict()
    })

# 用户相关接口
@api_bp.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({"status": "error", "message": "用户不存在"}), 404
    return jsonify({"status": "success", "data": user.to_dict()})

@api_bp.route('/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({"status": "error", "message": "用户不存在"}), 404
    
    data = request.json
    
    try:
        # 更新基本信息
        if 'name' in data:
            user.name = data['name']
        if 'avatar' in data:
            user.avatar = data['avatar']
        if 'bio' in data:
            user.bio = data['bio']
        if 'gender' in data:
            user.gender = data['gender']
        if 'age' in data:
            user.age = data['age']
        
        # 更新关联信息
        if 'mbti' in data:
            mbti = MbtiType.query.filter_by(name=data['mbti']).first()
            if mbti:
                user.mbti_id = mbti.id
        
        if 'travelDestination' in data:
            dest = Destination.query.filter_by(name=data['travelDestination']).first()
            if dest:
                user.travel_destination_id = dest.id
        
        if 'schedule' in data:
            schedule = Schedule.query.filter_by(name=data['schedule']).first()
            if schedule:
                user.schedule_id = schedule.id
        
        if 'budget' in data:
            budget = Budget.query.filter_by(name=data['budget']).first()
            if budget:
                user.budget_id = budget.id
        
        # 更新兴趣爱好
        if 'hobbies' in data:
            # 先清除现有兴趣
            delete_stmt = db.delete(user_hobby).where(user_hobby.c.user_id == user_id)
            result = db.session.execute(delete_stmt)
            db.session.commit()
            # 添加新兴趣
            for hobby_name in data['hobbies']:
                hobby = Hobby.query.filter_by(name=hobby_name).first()
                if hobby:
                    user.hobbies.append(hobby)
        
        db.session.commit()
        return jsonify({"status": "success", "data": user.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500

# 匹配相关接口
@api_bp.route('/users/<int:user_id>/matches', methods=['GET'])
def get_matches(user_id):
    matches = MatchRecord.query.filter_by(user_id=user_id, is_valid=True).all()
    return jsonify({
        "status": "success", 
        "data": [match.to_dict(include_user=True) for match in matches]
    })

@api_bp.route('/users/<int:user_id>/matches', methods=['POST'])
def create_matches(user_id):
    try:
        matches = find_matches(user_id)
        return jsonify({
            "status": "success", 
            "count": len(matches),
            "data": [match.to_dict(include_user=True) for match in matches]
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# 队伍相关接口
@api_bp.route('/teams', methods=['GET'])
def get_teams():
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({"status": "error", "message": "缺少用户ID"}), 400
    
    # 我创建的队伍
    captain_teams = Team.query.filter_by(captain_id=user_id).all()
    
    # 我加入的队伍
    user = User.query.get(user_id)
    if not user:
        return jsonify({"status": "error", "message": "用户不存在"}), 404
    
    member_teams = user.joined_teams.filter(Team.captain_id != user_id).all()
    #print([team.to_dict() for team in captain_teams])
    
    return jsonify({
        "status": "success",
        "captainTeams": [team.to_dict() for team in captain_teams],
        "memberTeams": [team.to_dict() for team in member_teams]
    })

@api_bp.route('/teams', methods=['POST'])
def create_team():
    data = request.json
    
    if not data.get('name') or not data.get('captainId'):
        return jsonify({"status": "error", "message": "队伍名称和队长ID不能为空"}), 400
    captain_teams = Team.query.with_entities(Team.name).filter_by(captain_id=data['captainId']).all()
    for team in captain_teams:
        if team == data['name']:
            return jsonify({"status": "error", "message": "已经创建过同名队伍"}), 400
    try:
        # 创建队伍
        team = Team(
            name=data['name'],
            captain_id=data['captainId']
        )
        db.session.add(team)
        db.session.commit()
        
        # 添加队长为成员
        captain = User.query.get(data['captainId'])
        if captain:
            team.members.append(captain)
            db.session.commit()
        
        return jsonify({"status": "success", "data": team.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500

@api_bp.route('/teams/<int:team_id>', methods=['DELETE'])
def delete_team(team_id):
    team = Team.query.get(team_id)
    if not team:
        return jsonify({"status": "error", "message": "队伍不存在"}), 404
    
    user_id = request.args.get('user_id')
    if not user_id or team.captain_id != int(user_id):
        return jsonify({"status": "error", "message": "只有队长可以删除队伍"}), 403
    
    try:
        db.session.delete(team)
        db.session.commit()
        return jsonify({"status": "success", "message": "队伍已删除"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500

@api_bp.route('/teams/<int:team_id>/members', methods=['POST'])
def add_team_member(team_id):
    data = request.json
    user_id = data.get('userId')
    
    if not user_id:
        return jsonify({"status": "error", "message": "用户ID不能为空"}), 400
    
    team = Team.query.get(team_id)
    if not team:
        return jsonify({"status": "error", "message": "队伍不存在"}), 404
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({"status": "error", "message": "用户不存在"}), 404
    
    # 检查用户是否已在队伍中
    if user in team.members:
        return jsonify({"status": "error", "message": "用户已在队伍中"}), 400
    
    try:
        team.members.append(user)
        db.session.commit()
        return jsonify({"status": "success", "data": team.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500

@api_bp.route('/teams/<int:team_id>/members/<int:user_id>', methods=['DELETE'])
def remove_team_member(team_id, user_id):
    team = Team.query.get(team_id)
    if not team:
        return jsonify({"status": "error", "message": "队伍不存在"}), 404
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({"status": "error", "message": "用户不存在"}), 404
    
    # 检查用户是否在队伍中
    if user not in team.members:
        return jsonify({"status": "error", "message": "用户不在队伍中"}), 400
    
    # 检查权限
    requester_id = request.args.get('requester_id')
    if not requester_id:
        return jsonify({"status": "error", "message": "请求者ID不能为空"}), 400
    
    # 只有队长可以踢人，或者用户可以自己离开
    if int(requester_id) != team.captain_id and int(requester_id) != user_id:
        return jsonify({"status": "error", "message": "没有权限执行此操作"}), 403
    
    # 队长不能踢自己
    if int(requester_id) == team.captain_id and user_id == team.captain_id:
        return jsonify({"status": "error", "message": "队长不能踢出自己"}), 400
    
    try:
        team.members.remove(user)
        db.session.commit()
        return jsonify({"status": "success", "data": team.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500

# 消息相关接口
'''@api_bp.route('/teams/<int:team_id>/messages', methods=['GET'])
def get_team_messages(team_id):
    team = Team.query.get(team_id)
    if not team:
        return jsonify({"status": "error", "message": "队伍不存在"}), 404
    
    messages = Message.query.filter_by(team_id=team_id).order_by(Message.send_time).all()
    return jsonify({
        "status": "success",
        "data": [msg.to_dict() for msg in messages]
    })
    '''
# 新增/修改：获取队伍消息（支持按lastMsgId筛选新消息）
@api_bp.route('/teams/<int:team_id>/messages', methods=['GET'])
def get_team_messages(team_id):
    # 1. 获取前端传递的lastMsgId（默认0，即全量加载）
    last_msg_id = request.args.get('lastMsgId', '0')
    last_msg_id = int(last_msg_id) if last_msg_id.isdigit() else 0
    
    # 2. 查询该队伍的消息（只取比last_msg_id大的消息，按时间升序）
    messages = Message.query.filter(
        Message.team_id == team_id,
        Message.id> last_msg_id  # 增量筛选：只返回新消息
    ).order_by(Message.send_time).all()
    
    
    return jsonify({"status": "success", "data": [msg.to_dict() for msg in messages]}), 200


@api_bp.route('/teams/<int:team_id>/messages', methods=['POST'])
def send_team_message(team_id):
    data = request.json
    
    if not data.get('senderId') or not data.get('content'):
        return jsonify({"status": "error", "message": "发送者ID和消息内容不能为空"}), 400
    
    team = Team.query.get(team_id)
    if not team:
        return jsonify({"status": "error", "message": "队伍不存在"}), 404
    
    user = User.query.get(data['senderId'])
    if not user:
        return jsonify({"status": "error", "message": "用户不存在"}), 404
    
    # 检查用户是否在队伍中
    if user not in team.members:
        return jsonify({"status": "error", "message": "只有队伍成员可以发送消息"}), 403
    
    try:
        message = Message(
            team_id=team_id,
            sender_id=data['senderId'],
            content=data['content']
        )
        db.session.add(message)
        db.session.commit()
        return jsonify({"status": "success", "data": message.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500

# 字典数据接口
@api_bp.route('/dictionaries', methods=['GET'])
def get_dictionaries():
    try:
        mbti_types = [m.name for m in MbtiType.query.all()]
        hobbies = [h.name for h in Hobby.query.all()]
        destinations = [d.name for d in Destination.query.all()]
        schedules = [s.name for s in Schedule.query.all()]
        budgets = [b.name for b in Budget.query.all()]
        
        return jsonify({
            "status": "success",
            "data": {
                "mbtiTypes": mbti_types,
                "hobbies": hobbies,
                "destinations": destinations,
                "schedules": schedules,
                "budgets": budgets
            }
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
