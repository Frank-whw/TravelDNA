import argparse
import random
from collections import defaultdict
from datetime import datetime, timedelta

from faker import Faker

from app import db
from app.models import (
    Budget,
    Destination,
    Hobby,
    MatchRecord,
    Message,
    Schedule,
    Team,
    User,
    MbtiType,
    team_member,
    user_hobby,
)
from app.utils import calculate_match_score, init_default_data

fake = Faker("zh_CN")

TEAM_TOPICS = [
    "城市探索",
    "美食狂欢",
    "户外探险",
    "亲子出游",
    "摄影打卡",
    "文化漫步",
    "慢节奏度假",
    "海岛计划",
    "滑雪同好",
    "房车旅队",
]

TEAM_NAME_TEMPLATES = [
    "{city}{topic}团",
    "{topic}小分队",
    "{city}{number}号旅行队",
    "{topic}{emoji}队",
    "{season}{topic}组",
]

SEASON_WORDS = ["春日", "夏日", "秋日", "冬日"]
EMOJIS = ["🌟", "✨", "🧭", "🍜", "🏞️", "🎒", "🚞", "🛶", "🗺️", "🏖️"]

MESSAGE_SNIPPETS = [
    "有人知道当地有什么必去的吗？",
    "我可以负责拍照，欢迎一起打卡～",
    "机票我已经看好了，大家确认一下日期。",
    "建议早点预订酒店，节假日可能会涨价。",
    "我们要不要安排一顿当地特色餐厅？",
    "有没有推荐的夜景路线，想拍照。",
    "早起党在此，行程可以安排紧凑一点吗？",
    "有朋友带孩子吗？我们可以一起商量亲子行程。",
    "交通卡提前准备好，地铁会更方便。",
    "天气好像会下雨，带上雨具比较保险。",
    "我周末有时间，可以一起线下碰面聊计划。",
]


def purge_existing_data():
    """清空主要业务数据，避免重复插入"""
    print("清理历史数据...")
    db.session.execute(team_member.delete())
    db.session.execute(user_hobby.delete())
    Message.query.delete()
    MatchRecord.query.delete()
    Team.query.delete()
    User.query.delete()
    db.session.commit()
    print("数据清理完成。")


def ensure_dictionary_data():
    """确保基础字典数据存在"""
    init_default_data()


def load_dictionary_data():
    mbti_types = MbtiType.query.all()
    hobbies = Hobby.query.all()
    destinations = Destination.query.all()
    schedules = Schedule.query.all()
    budgets = Budget.query.all()
    if not all([mbti_types, hobbies, destinations, schedules, budgets]):
        raise RuntimeError("字典数据不完整，请先确保 /init-data 已执行。")
    return mbti_types, hobbies, destinations, schedules, budgets


def generate_random_users(count):
    mbti_types, hobbies, destinations, schedules, budgets = load_dictionary_data()
    users = []
    for _ in range(count):
        gender = random.choice(["男", "女", "其他"])
        age = random.randint(18, 60)
        mbti = random.choice(mbti_types)
        destination = random.choice(destinations)
        schedule = random.choice(schedules)
        budget = random.choice(budgets)
        selected_hobbies = random.sample(hobbies, random.randint(2, min(6, len(hobbies))))

        user = User(
            name=fake.name(),
            avatar=f"https://picsum.photos/seed/{fake.uuid4()}/200/200",
            bio=fake.text(max_nb_chars=120),
            gender=gender,
            age=age,
            mbti_id=mbti.id,
            travel_destination_id=destination.id,
            schedule_id=schedule.id,
            budget_id=budget.id,
        )
        for hobby in selected_hobbies:
            user.hobbies.append(hobby)
        users.append(user)

    db.session.add_all(users)
    db.session.commit()
    print(f"生成用户：{len(users)} 条")
    return users


def random_team_name(city: str) -> str:
    template = random.choice(TEAM_NAME_TEMPLATES)
    topic = random.choice(TEAM_TOPICS)
    number = random.randint(1, 99)
    emoji = random.choice(EMOJIS)
    season = random.choice(SEASON_WORDS)
    return template.format(city=city, topic=topic, number=number, emoji=emoji, season=season)


def generate_teams(team_count, min_members, max_members):
    users = User.query.all()
    if len(users) < min_members:
        raise RuntimeError("用户数量不足，无法组建队伍。")

    used_captains = set()
    teams = []
    for _ in range(team_count):
        captain = random.choice(users)
        attempts = 0
        while captain.id in used_captains and attempts < 5:
            captain = random.choice(users)
            attempts += 1
        used_captains.add(captain.id)

        city = captain.travel_destination.name if captain.travel_destination else "旅行"
        name = random_team_name(city)

        team = Team(name=name, captain_id=captain.id)
        team.members.append(captain)

        member_count = random.randint(min_members, max_members)
        candidates = [u for u in users if u.id != captain.id]
        selected_members = random.sample(candidates, min(member_count - 1, len(candidates)))
        for member in selected_members:
            team.members.append(member)

        teams.append(team)

    db.session.add_all(teams)
    db.session.commit()
    print(f"生成队伍：{len(teams)} 支")
    return teams


def generate_team_messages(teams, avg_messages=25):
    created = 0
    for team in teams:
        member_ids = [member.id for member in team.members]
        if not member_ids:
            continue
        message_count = max(5, int(random.gauss(avg_messages, avg_messages * 0.3)))
        base_time = datetime.utcnow() - timedelta(days=random.randint(0, 10))
        for i in range(message_count):
            sender_id = random.choice(member_ids)
            content = random.choice(MESSAGE_SNIPPETS)
            message = Message(
                team_id=team.id,
                sender_id=sender_id,
                content=content,
                send_time=base_time + timedelta(minutes=i * random.randint(3, 15)),
            )
            db.session.add(message)
            created += 1
    db.session.commit()
    print(f"生成消息：{created} 条")


def generate_match_records(max_candidates=12, min_score=60):
    users = User.query.all()
    created = 0
    updated = 0
    for user in users:
        others = [u for u in users if u.id != user.id]
        sampled = random.sample(others, min(max_candidates, len(others)))
        for candidate in sampled:
            score = calculate_match_score(user, candidate)
            existing = MatchRecord.query.filter_by(user_id=user.id, matched_user_id=candidate.id).first()
            if score >= min_score:
                if existing:
                    existing.matching_score = score
                    existing.is_valid = True
                    updated += 1
                else:
                    db.session.add(
                        MatchRecord(
                            user_id=user.id,
                            matched_user_id=candidate.id,
                            matching_score=score,
                            is_valid=True,
                        )
                    )
                    created += 1
            elif existing and existing.is_valid:
                existing.matching_score = score
                existing.is_valid = False
                updated += 1
    db.session.commit()
    print(f"生成匹配记录：新增 {created} 条，更新 {updated} 条")


def build_usage_heatmap(teams):
    """构造简单的统计，用于确认数据量"""
    city_counts = defaultdict(int)
    for team in teams:
        for member in team.members:
            if member.travel_destination:
                city_counts[member.travel_destination.name] += 1
    top_cities = sorted(city_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    if top_cities:
        print("成员热门目的地 TOP10：")
        for city, count in top_cities:
            print(f"  - {city}: {count} 人次")
    return top_cities


def parse_args():
    parser = argparse.ArgumentParser(description="为社区模块批量生成僵尸数据")
    parser.add_argument("--users", type=int, default=300, help="生成用户数量")
    parser.add_argument("--teams", type=int, default=80, help="生成队伍数量")
    parser.add_argument("--min-members", type=int, default=3, help="每个队伍最少成员数（含队长）")
    parser.add_argument("--max-members", type=int, default=8, help="每个队伍最多成员数")
    parser.add_argument("--messages-per-team", type=int, default=30, help="每支队伍平均消息数")
    parser.add_argument("--matches-per-user", type=int, default=12, help="每个用户尝试匹配的候选数量")
    parser.add_argument("--min-match-score", type=int, default=60, help="匹配成立的最低分")
    parser.add_argument("--purge", action="store_true", help="生成前清空历史数据")
    return parser.parse_args()


def seed_mock_data(
    users: int = 300,
    teams: int = 80,
    min_members: int = 3,
    max_members: int = 8,
    messages_per_team: int = 30,
    matches_per_user: int = 12,
    min_match_score: int = 60,
    purge: bool = False,
):
    ensure_dictionary_data()
    if purge:
        purge_existing_data()

    generated_users = generate_random_users(users)
    generated_teams = generate_teams(teams, min_members, max_members)
    generate_team_messages(generated_teams, avg_messages=messages_per_team)
    generate_match_records(max_candidates=matches_per_user, min_score=min_match_score)
    top_cities = build_usage_heatmap(generated_teams)

    stats = {
        "users": len(generated_users),
        "teams": len(generated_teams),
        "messages_per_team": messages_per_team,
        "matches_per_user": matches_per_user,
    }
    if top_cities:
        stats["top_cities"] = top_cities
    return stats


def main():
    args = parse_args()
    stats = seed_mock_data(
        users=args.users,
        teams=args.teams,
        min_members=args.min_members,
        max_members=args.max_members,
        messages_per_team=args.messages_per_team,
        matches_per_user=args.matches_per_user,
        min_match_score=args.min_match_score,
        purge=args.purge,
    )
    print("数据填充完成。统计：")
    print(f"  - 用户：{stats['users']} 个")
    print(f"  - 队伍：{stats['teams']} 支")
    print(f"  - 每队平均消息：{stats['messages_per_team']} 条")
    print(f"  - 每用户匹配候选：{stats['matches_per_user']} 个")
    if stats.get("top_cities"):
        print("  - 热门目的地 TOP10：")
        for city, count in stats["top_cities"]:
            print(f"      · {city}: {count} 人次")


if __name__ == "__main__":
    from app import create_app

    app = create_app()
    with app.app_context():
        main()
