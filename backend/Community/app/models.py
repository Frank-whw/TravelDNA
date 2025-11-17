from datetime import datetime
from app import db

# 中间表 - 用户和兴趣的多对多关系
user_hobby = db.Table('user_hobby',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('hobby_id', db.Integer, db.ForeignKey('hobby.id'), primary_key=True),
    db.Column('create_time', db.DateTime, default=datetime.utcnow)
)

# 中间表 - 队伍和成员的多对多关系
team_member = db.Table('team_member',
    db.Column('team_id', db.Integer, db.ForeignKey('team.id'), primary_key=True),
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('joined_at', db.DateTime, default=datetime.utcnow)
)

class MbtiType(db.Model):
    __tablename__ = 'mbti_type'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(10), unique=True, nullable=False)
    create_time = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 关系
    users = db.relationship('User', backref='mbti', lazy='dynamic')
    
    def __repr__(self):
        return f'<MbtiType {self.name}>'

class Hobby(db.Model):
    __tablename__ = 'hobby'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), unique=True, nullable=False)
    create_time = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 关系
    users = db.relationship('User', secondary=user_hobby, backref=db.backref('hobbies', lazy='dynamic'), lazy='dynamic')
    
    def __repr__(self):
        return f'<Hobby {self.name}>'

class Destination(db.Model):
    __tablename__ = 'destination'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), unique=True, nullable=False)
    create_time = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 关系
    users = db.relationship('User', backref='travel_destination', lazy='dynamic')
    
    def __repr__(self):
        return f'<Destination {self.name}>'

class Schedule(db.Model):
    __tablename__ = 'schedule'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), unique=True, nullable=False)
    create_time = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 关系
    users = db.relationship('User', backref='schedule_type', lazy='dynamic')
    
    def __repr__(self):
        return f'<Schedule {self.name}>'

class Budget(db.Model):
    __tablename__ = 'budget'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), unique=True, nullable=False)
    create_time = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 关系
    users = db.relationship('User', backref='budget_type', lazy='dynamic')
    
    def __repr__(self):
        return f'<Budget {self.name}>'

class User(db.Model):
    __tablename__ = 'user'
    
    id = db.Column(db.Integer, primary_key=True)
    # 账号相关字段
    email = db.Column(db.String(255), unique=True, nullable=True)
    phone = db.Column(db.String(20), unique=True, nullable=True)
    password_hash = db.Column(db.String(255), nullable=True)
    salt = db.Column(db.String(32), nullable=True)
    status = db.Column(db.String(20), default='active', nullable=False)  # active, inactive, banned
    # 用户信息字段
    name = db.Column(db.String(50), nullable=False)
    avatar = db.Column(db.String(255), default='https://space.coze.cn/api/coze_space/gen_image?image_size=square&prompt=User%20avatar%2C%20person%20portrait%2C%20cartoon%20style&sign=a9b44dd75e1d6cd26a8cf0935243421c')
    bio = db.Column(db.Text, nullable=True)
    gender = db.Column(db.String(10), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    mbti_id = db.Column(db.Integer, db.ForeignKey('mbti_type.id'))
    travel_destination_id = db.Column(db.Integer, db.ForeignKey('destination.id'))
    schedule_id = db.Column(db.Integer, db.ForeignKey('schedule.id'))
    budget_id = db.Column(db.Integer, db.ForeignKey('budget.id'))
    create_time = db.Column(db.DateTime, default=datetime.utcnow)
    update_time = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 添加检查约束：email 和 phone 至少有一个
    __table_args__ = (
        db.CheckConstraint('(email IS NOT NULL) OR (phone IS NOT NULL)', name='check_email_or_phone'),
    )
    
    # 关系
    created_teams = db.relationship('Team', backref='captain', lazy='dynamic')
    joined_teams = db.relationship('Team', secondary=team_member, backref=db.backref('members', lazy='dynamic'), lazy='dynamic')
    sent_matches = db.relationship('MatchRecord', foreign_keys='MatchRecord.user_id', backref='matcher', lazy='dynamic')
    received_matches = db.relationship('MatchRecord', foreign_keys='MatchRecord.matched_user_id', backref='matched_user', lazy='dynamic')
    messages = db.relationship('Message', backref='sender', lazy='dynamic')
    
    def __repr__(self):
        return f'<User {self.name}>'
    
    def to_dict(self, include_sensitive=False):
        result = {
            'id': self.id,
            'name': self.name,
            'avatar': self.avatar,
            'bio': self.bio,
            'gender': self.gender,
            'age': self.age,
            'mbti': self.mbti.name if self.mbti else None,
            'hobbies': [hobby.name for hobby in self.hobbies.all()],
            'travelDestination': self.travel_destination.name if self.travel_destination else None,
            'schedule': self.schedule_type.name if self.schedule_type else None,
            'budget': self.budget_type.name if self.budget_type else None,
            'status': self.status,
            'createTime': self.create_time.isoformat() if self.create_time else None
        }
        # 只在需要时包含敏感信息
        if include_sensitive:
            result['email'] = self.email
            result['phone'] = self.phone
        return result

class Team(db.Model):
    __tablename__ = 'team'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    captain_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    create_time = db.Column(db.DateTime, default=datetime.utcnow)
    update_time = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    messages = db.relationship('Message', backref='team', lazy='dynamic')
    
    def __repr__(self):
        return f'<Team {self.name}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'captainId': self.captain_id,
            'members': [member.to_dict() for member in self.members.all()],
            'memberCount': self.members.count()
        }

class MatchRecord(db.Model):
    __tablename__ = 'match_record'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    matched_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    matching_score = db.Column(db.Integer, nullable=False)
    match_time = db.Column(db.DateTime, default=datetime.utcnow)
    is_valid = db.Column(db.Boolean, default=True)
    
    __table_args__ = (
        db.CheckConstraint('user_id != matched_user_id', name='check_not_self_match'),
        db.UniqueConstraint('user_id', 'matched_user_id', name='unique_user_match'),
    )
    
    def __repr__(self):
        return f'<MatchRecord {self.user_id} -> {self.matched_user_id} ({self.matching_score}%)>'
    
    def to_dict(self, include_user=False):
        result = {
            'id': self.id,
            'userId': self.user_id,
            'matchedUserId': self.matched_user_id,
            'matchingScore': self.matching_score,
            'matchTime': self.match_time.isoformat(),
            'isValid': self.is_valid
        }
        
        if include_user and self.matched_user:
            user_data = self.matched_user.to_dict()
            user_data['matchingScore'] = self.matching_score
            result['user'] = user_data
            
        return result

class Message(db.Model):
    __tablename__ = 'message'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    send_time = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Message {self.id} in team {self.team_id}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'teamId': self.team_id,
            'senderId': self.sender_id,
            'senderName': self.sender.name if self.sender else None,
            'content': self.content,
            'timestamp': self.send_time.strftime('%H:%M')
        }
