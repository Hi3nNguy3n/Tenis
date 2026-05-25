# backend/app/crud/crud_player.py
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc
from app.models.models import Player, User, Match, Registration, Tournament, Court, Role
from app.schemas.player_schemas import PlayerUpdate

PLAYER_STAT_FIELDS = [
    "aces",
    "double_faults",
    "first_serve_pct",
    "first_serve_points_won_pct",
    "second_serve_points_won_pct",
    "break_points_faced",
    "break_points_saved_pct",
    "service_games_played",
    "service_games_won_pct",
    "total_service_points_won_pct",
    "first_serve_return_points_won_pct",
    "second_serve_return_points_won_pct",
    "break_points_opportunities",
    "break_points_converted_pct",
    "return_games_played",
    "return_games_won_pct",
    "return_points_won_pct",
    "total_points_won_pct",
]

def _apply_player_stat_updates(player: Player, update_data: PlayerUpdate):
    for field in PLAYER_STAT_FIELDS:
        value = getattr(update_data, field, None)
        if value is not None:
            setattr(player, field, value)

def get_player_by_user_id(db: Session, user_id: int):
    return db.query(Player).filter(Player.user_id == user_id).first()

def update_player_profile(db: Session, user: User, update_data: PlayerUpdate):
    if update_data.full_name: user.full_name = update_data.full_name
    if update_data.phone: user.phone = update_data.phone
    if update_data.province: user.province = update_data.province 
    if update_data.gender: user.gender = update_data.gender
    if update_data.date_of_birth: user.date_of_birth = update_data.date_of_birth
    
    # BỔ SUNG DÒNG NÀY ĐỂ LƯU AVATAR VÀO BẢNG USER
    if hasattr(update_data, 'avatar_url') and update_data.avatar_url is not None:
        user.avatar_url = update_data.avatar_url

    player = get_player_by_user_id(db, user.id)
    if player:
        if update_data.gender: player.gender = update_data.gender
        if update_data.date_of_birth: player.date_of_birth = update_data.date_of_birth
        if update_data.play_hand: player.play_hand = update_data.play_hand
        if update_data.skill_level: player.skill_level = update_data.skill_level
        if update_data.preferred_category: player.preferred_category = update_data.preferred_category
        if update_data.bio is not None: player.bio = update_data.bio
        if update_data.height_cm is not None: player.height_cm = update_data.height_cm
        if update_data.weight_kg is not None: player.weight_kg = update_data.weight_kg
        _apply_player_stat_updates(player, update_data)

    db.commit()
    db.refresh(user)
    return user, player

def update_user_avatar(db: Session, user: User, avatar_url: str):
    user.avatar_url = avatar_url
    db.commit()
    db.refresh(user)
    return user

def get_players_list(db: Session, search: str = None, skill: str = None, status: str = None):
    # Lấy cả Player và User trong 1 lần query
    query = db.query(Player, User).join(User, Player.user_id == User.id)
    
    if search:
        query = query.filter(or_(
            User.full_name.ilike(f"%{search}%"),
            User.email.ilike(f"%{search}%"),
            User.phone.ilike(f"%{search}%")
        ))
    if skill:
        query = query.filter(Player.skill_level == skill)
    if status is not None:
        is_active = status.lower() == 'active'
        query = query.filter(User.is_active == is_active)
        
    return query.all()

def admin_update_player_data(db: Session, player_id: int, update_data: PlayerUpdate):
    # 1. Tìm thông tin Player
    player = db.query(Player).filter(Player.id == player_id).first()
    if not player:
        return None
        
    # 2. Tìm thông tin User tương ứng
    user = db.query(User).filter(User.id == player.user_id).first()
    
    if user:
        # Cập nhật thông tin cơ bản
        if update_data.full_name is not None: user.full_name = update_data.full_name
        if update_data.phone is not None: user.phone = update_data.phone
        if update_data.province is not None: user.province = update_data.province
        if update_data.gender is not None: user.gender = update_data.gender
        if update_data.date_of_birth is not None: user.date_of_birth = update_data.date_of_birth
        
        # BỔ SUNG: Cập nhật Ảnh đại diện & Trạng thái tài khoản
        if hasattr(update_data, 'avatar_url') and update_data.avatar_url is not None:
            user.avatar_url = update_data.avatar_url
        if hasattr(update_data, 'is_active') and update_data.is_active is not None:
            user.is_active = update_data.is_active

    # 3. Cập nhật thông tin Player (VĐV)
    if update_data.gender is not None: player.gender = update_data.gender
    if update_data.date_of_birth is not None: player.date_of_birth = update_data.date_of_birth
    if update_data.play_hand is not None: player.play_hand = update_data.play_hand
    if update_data.skill_level is not None: player.skill_level = update_data.skill_level
    if update_data.preferred_category is not None: player.preferred_category = update_data.preferred_category
    if update_data.bio is not None: player.bio = update_data.bio
    if update_data.height_cm is not None: player.height_cm = update_data.height_cm
    if update_data.weight_kg is not None: player.weight_kg = update_data.weight_kg
    _apply_player_stat_updates(player, update_data)

    db.commit()
    db.refresh(player)
    db.refresh(user)
    
    return player

def get_player_rankings(db: Session, category: str = None, province: str = None, limit: int = None):
    query = db.query(Player, User).join(User, Player.user_id == User.id).outerjoin(
        Role, User.role_id == Role.id
    ).filter(
        User.is_active == True,
        User.account_type != "admin",
        or_(Role.id.is_(None), Role.role_key != "admin")
    )
    if category:
        query = query.filter(Player.preferred_category == category)
    if province:
        query = query.filter(User.province == province)

    query = query.order_by(desc(Player.elo_points), desc(Player.wins))
    if limit:
        query = query.limit(limit)
    return query.all()

# --- CÁC HÀM PHỤ TRỢ CHO LỊCH SỬ THI ĐẤU ---
def get_player_registrations(db: Session, player_id: int):
    reg_ids = db.query(Registration.id).filter(Registration.player_id == player_id).all()
    # Tìm cả các lượt đăng ký mà người chơi này là partner (đồng đội)
    partner_regs = db.query(Registration.id).filter(Registration.partner_player_id == player_id).all()
    all_regs = list(set([r[0] for r in reg_ids] + [r[0] for r in partner_regs]))
    return all_regs

def get_all_player_matches(db: Session, player_id: int, reg_ids: list):
    query = db.query(Match, Tournament, Court).outerjoin(
        Tournament, Match.tournament_id == Tournament.id
    ).outerjoin(
        Court, Match.court_id == Court.id
    )
    
    conditions = [
        Match.player_a_id == player_id,
        Match.player_b_id == player_id,
        Match.player_a2_id == player_id,
        Match.player_b2_id == player_id
    ]
    if reg_ids:
        conditions.append(Match.side_a_registration_id.in_(reg_ids))
        conditions.append(Match.side_b_registration_id.in_(reg_ids))
        
    return query.filter(or_(*conditions)).order_by(desc(Match.start_time), desc(Match.created_at)).all()

def get_matches_by_registrations(db: Session, reg_ids: list):
    if not reg_ids: return []
    return db.query(Match, Tournament, Court).join(
        Tournament, Match.tournament_id == Tournament.id
    ).outerjoin(
        Court, Match.court_id == Court.id
    ).filter(
        or_(
            Match.side_a_registration_id.in_(reg_ids),
            Match.side_b_registration_id.in_(reg_ids)
        )
    ).order_by(desc(Match.created_at)).all()

def get_opponent_user_by_reg_id(db: Session, reg_id: int):
    if not reg_id: return None
    return db.query(User).join(
        Player, Player.user_id == User.id
    ).join(
        Registration, Registration.player_id == Player.id
    ).filter(Registration.id == reg_id).first()

def search_players(db: Session, keyword: str, limit: int = 10):
    # Join Player với User để lấy cả 2 thông tin
    query = db.query(Player, User).join(User, Player.user_id == User.id)

    if keyword.isdigit():
        # Nếu nhập số, tìm theo User ID (để đồng bộ với Chat)
        results = query.filter(User.id == int(keyword)).all()
    else:
        # Tìm theo tên trong bảng User
        results = query.filter(User.full_name.ilike(f"%{keyword}%")).limit(limit).all()

    # QUAN TRỌNG: Trả về một danh sách các Dictionary
    # Trong đó "id" PHẢI LÀ u.id (User ID) để Chat gửi đúng người
    return [
        {
            "id": u.id, 
            "player_id": p.id,
            "full_name": u.full_name,
            "phone": u.phone,
            "avatar_url": u.avatar_url,
            "level": p.skill_level
        } for p, u in results
    ]

def get_player_by_id(db: Session, player_id: int):
    # player_id ở đây được hiểu là User ID để đồng bộ toàn hệ thống
    result = db.query(Player, User).join(User, Player.user_id == User.id).filter(User.id == player_id).first()
    if not result:
        return None
    p, u = result
    
    # Tính toán win rate
    total = p.wins + p.losses
    win_rate = round((p.wins / total * 100), 1) if total > 0 else 0
    
    # Tính toán thứ hạng
    rank = db.query(Player).filter(
        or_(
            Player.elo_points > p.elo_points,
            (Player.elo_points == p.elo_points) & (Player.wins > p.wins)
        )
    ).count() + 1
    
    return {
        "user": {
            "id": u.id,
            "full_name": u.full_name,
            "email": u.email,
            "phone": u.phone,
            "avatar_url": u.avatar_url,
            "province": u.province,
            "gender": u.gender,
            "date_of_birth": u.date_of_birth
        },
        "player_profile": {
            "id": p.id,
            "rank": rank,
            "elo_points": p.elo_points,
            "wins": p.wins,
            "losses": p.losses,
            "matches_played": p.matches_played,
            "win_rate": win_rate,
            "gender": p.gender or u.gender, # Fallback về user gender
            "date_of_birth": p.date_of_birth or u.date_of_birth, # Fallback về user dob
            "play_hand": p.play_hand,
            "skill_level": p.skill_level,
            "preferred_category": p.preferred_category,
            "bio": p.bio,
            "height_cm": p.height_cm,
            "weight_kg": p.weight_kg,
            **{field: float(getattr(p, field) or 0) for field in PLAYER_STAT_FIELDS}
        }
    }
