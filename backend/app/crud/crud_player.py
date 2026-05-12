# backend/app/crud/crud_player.py
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc
from app.models.models import Player, User, Match, Registration, Tournament, Court
from app.schemas.player_schemas import PlayerUpdate

def get_player_by_user_id(db: Session, user_id: int):
    return db.query(Player).filter(Player.user_id == user_id).first()

def update_player_profile(db: Session, user: User, update_data: PlayerUpdate):
    if update_data.full_name: user.full_name = update_data.full_name
    if update_data.phone: user.phone = update_data.phone
    if update_data.province: user.province = update_data.province 
    
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

    db.commit()
    db.refresh(player)
    db.refresh(user)
    
    return player

def get_player_rankings(db: Session, category: str = None, province: str = None):
    query = db.query(Player, User).join(User, Player.user_id == User.id).filter(
        User.is_active == True
    )
    if category:
        query = query.filter(Player.preferred_category == category)
    if province:
        query = query.filter(User.province == province)

    return query.order_by(desc(Player.elo_points), desc(Player.wins)).all()

# --- CÁC HÀM PHỤ TRỢ CHO LỊCH SỬ THI ĐẤU ---
def get_player_registrations(db: Session, player_id: int):
    reg_ids = db.query(Registration.id).filter(Registration.player_id == player_id).all()
    return [r[0] for r in reg_ids]

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
    return db.query(User).join(Player).join(Registration).filter(Registration.id == reg_id).first()

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
            "full_name": u.full_name,
            "avatar_url": u.avatar_url,
            "level": p.skill_level
        } for p, u in results
    ]

def get_player_by_id(db: Session, player_id: int):
    # player_id ở đây bây giờ được hiểu là User ID
    result = db.query(Player, User).join(User, Player.user_id == User.id).filter(User.id == player_id).first()
    if not result:
        return None
    p, u = result
    return {
        "id": u.id,
        "full_name": u.full_name,
        "avatar_url": u.avatar_url,
        "level": p.skill_level
    }