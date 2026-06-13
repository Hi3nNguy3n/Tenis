# backend/app/models/models.py

from sqlalchemy import Column, Integer, BigInteger, String, Boolean, DateTime, Date, ForeignKey, Text, Numeric, SmallInteger
from sqlalchemy.dialects.postgresql import JSONB  # Khuyên dùng JSONB cho PostgreSQL để query nhanh hơn JSON thường
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.database import Base

# ==========================================
# MODULE 5: AUTH & ACCOUNT (Tài khoản & Phân quyền)
# ==========================================

class Role(Base):
    __tablename__ = "roles"
    id = Column(BigInteger, primary_key=True, index=True)
    role_key = Column(String(50), unique=True, nullable=False)
    role_name = Column(String(100), nullable=False)
    scope = Column(String(30), index=True, nullable=False)
    description = Column(String(255))
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class User(Base):
    __tablename__ = "users"
    id = Column(BigInteger, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    account_type = Column(String(30), index=True, nullable=False)
    full_name = Column(String(150), nullable=False)
    phone = Column(String(20), index=True)
    avatar_url = Column(String(500))
    province = Column(String(120), index=True)
    date_of_birth = Column(Date)
    gender = Column(String(20), index=True)
    is_active = Column(Boolean, default=True, index=True)
    is_verified = Column(Boolean, default=False, index=True)
    last_login_at = Column(DateTime, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, index=True)
    
    role_id = Column(BigInteger, ForeignKey("roles.id"), index=True, nullable=False)

class AuthOtp(Base):
    __tablename__ = "auth_otps"
    id = Column(BigInteger, primary_key=True, index=True)
    target_email = Column(String(255), index=True, nullable=False)
    otp_code = Column(String(10), nullable=False)
    purpose = Column(String(30), index=True, nullable=False)
    expired_at = Column(DateTime, index=True, nullable=False)
    is_used = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

# ==========================================
# MODULE 3: PLAYER (Hồ sơ Vận động viên & Đội)
# ==========================================

class Player(Base):
    __tablename__ = "players"
    id = Column(BigInteger, primary_key=True, index=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), unique=True, nullable=False)
    play_hand = Column(String(10), index=True)
    gender = Column(String(20), index=True)
    skill_level = Column(String(30), index=True)
    preferred_category = Column(String(20), index=True)
    elo_points = Column(Integer, default=1000, index=True, nullable=False)
    wins = Column(Integer, default=0, nullable=False)
    losses = Column(Integer, default=0, nullable=False)
    matches_played = Column(Integer, default=0, nullable=False)
    bio = Column(Text)
    admin_notes = Column(Text)
    height_cm = Column(Integer)
    weight_kg = Column(Integer)
    aces = Column(Integer, default=0, nullable=False)
    double_faults = Column(Integer, default=0, nullable=False)
    first_serve_pct = Column(Numeric(5, 2), default=0, nullable=False)
    first_serve_points_won_pct = Column(Numeric(5, 2), default=0, nullable=False)
    second_serve_points_won_pct = Column(Numeric(5, 2), default=0, nullable=False)
    break_points_faced = Column(Integer, default=0, nullable=False)
    break_points_saved_pct = Column(Numeric(5, 2), default=0, nullable=False)
    service_games_played = Column(Integer, default=0, nullable=False)
    service_games_won_pct = Column(Numeric(5, 2), default=0, nullable=False)
    total_service_points_won_pct = Column(Numeric(5, 2), default=0, nullable=False)
    first_serve_return_points_won_pct = Column(Numeric(5, 2), default=0, nullable=False)
    second_serve_return_points_won_pct = Column(Numeric(5, 2), default=0, nullable=False)
    break_points_opportunities = Column(Integer, default=0, nullable=False)
    break_points_converted_pct = Column(Numeric(5, 2), default=0, nullable=False)
    return_games_played = Column(Integer, default=0, nullable=False)
    return_games_won_pct = Column(Numeric(5, 2), default=0, nullable=False)
    return_points_won_pct = Column(Numeric(5, 2), default=0, nullable=False)
    total_points_won_pct = Column(Numeric(5, 2), default=0, nullable=False)
    date_of_birth = Column(Date)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, index=True)

class Team(Base):
    __tablename__ = "teams"
    id = Column(BigInteger, primary_key=True, index=True)
    team_name = Column(String(150), index=True)
    team_code = Column(String(50), unique=True)
    team_type = Column(String(20), index=True, nullable=False)
    created_by = Column(BigInteger, ForeignKey("users.id"), index=True)
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class TeamMember(Base):
    __tablename__ = "team_members"
    id = Column(BigInteger, primary_key=True, index=True)
    team_id = Column(BigInteger, ForeignKey("teams.id"), index=True, nullable=False)
    player_id = Column(BigInteger, ForeignKey("players.id"), index=True, nullable=False)
    member_order = Column(SmallInteger, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

# ==========================================
# MODULE 2: TOURNAMENT (Giải đấu & Đăng ký)
# ==========================================

class Tournament(Base):
    __tablename__ = "tournaments"
    id = Column(BigInteger, primary_key=True, index=True)
    name = Column(String(255), index=True, nullable=False)
    slug = Column(String(255), unique=True, nullable=False)
    category_type = Column(String(20), index=True, nullable=False)
    gender_division = Column(String(20), index=True, nullable=False)
    format_type = Column(String(20), index=True, nullable=False)
    draw_size = Column(Integer, nullable=False)
    registration_open_at = Column(DateTime, index=True)
    registration_close_at = Column(DateTime, index=True)
    start_date = Column(Date, index=True, nullable=False)
    end_date = Column(Date)
    status = Column(String(20), index=True, nullable=False)
    location = Column(String(255))
    surface_type = Column(String(30))
    entry_fee = Column(Numeric(15, 2))
    entry_fee_team = Column(Numeric(15, 2))
    max_participants = Column(Integer)
    description = Column(Text) # Thông tin chi tiết, điều lệ giải đấu
    banner_url = Column(String(255), nullable=True)
    display_order = Column(Integer, default=0, index=True, nullable=False)
    version = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    categories = relationship("TournamentCategory", back_populates="tournament")


class TournamentCategory(Base):
    __tablename__ = "tournament_categories"
    id = Column(BigInteger, primary_key=True, index=True)
    tournament_id = Column(BigInteger, ForeignKey("tournaments.id"), index=True, nullable=False)
    name = Column(String(150), nullable=False) # VD: Đôi Nam 1275, Đôi Nam Nữ 1200
    category_type = Column(String(50), nullable=False) # VD: mens_doubles, mixed_doubles, mens_singles
    max_points = Column(Integer) # VD: 1275
    max_participants = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    tournament = relationship("Tournament", back_populates="categories")


class Registration(Base):
    __tablename__ = "registrations"
    id = Column(BigInteger, primary_key=True, index=True)
    tournament_id = Column(BigInteger, ForeignKey("tournaments.id"), index=True, nullable=False)
    registrant_type = Column(String(20), index=True, nullable=False)
    player_id = Column(BigInteger, ForeignKey("players.id"), index=True)
    team_id = Column(BigInteger, ForeignKey("teams.id"), index=True)
    seed_no = Column(Integer)
    status = Column(String(20), index=True, nullable=False)
    payment_status = Column(String(20), index=True, nullable=False)
    hold_expires_at = Column(DateTime, index=True)
    registered_at = Column(DateTime, index=True, nullable=False)
    approved_at = Column(DateTime)
    notes = Column(String(255))
    group_code = Column(String(20))
    partner_name = Column(String(150))
    partner_phone = Column(String(20))
    partner_email = Column(String(255))
    partner_user_id = Column(BigInteger, ForeignKey("users.id"), index=True)
    partner_player_id = Column(BigInteger, ForeignKey("players.id"), index=True) # Map trực tiếp với Player profile
    tournament_category_id = Column(BigInteger, ForeignKey("tournament_categories.id"), index=True) # Đăng ký vào nội dung nào
    team_members_data = Column(JSONB)
    deleted_at = Column(DateTime, index=True)
    qr_code_url = Column(String(255))
    is_locked = Column(Boolean, default=False, server_default="false", nullable=False, index=True)
    
class Payment(Base):
    __tablename__ = "payments"
    id = Column(BigInteger, primary_key=True, index=True)
    registration_id = Column(BigInteger, ForeignKey("registrations.id"), index=True, nullable=True)
    challenge_id = Column(BigInteger, ForeignKey("match_challenges.id"), nullable=True)
    amount = Column(Numeric(15, 2), nullable=False)
    currency = Column(String(10), nullable=False)
    payment_method = Column(String(30), index=True, nullable=False)
    transaction_ref = Column(String(100), unique=True)
    status = Column(String(20), index=True, nullable=False)
    paid_at = Column(DateTime, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Court(Base):
    __tablename__ = "courts"
    id = Column(BigInteger, primary_key=True, index=True)
    court_name = Column(String(120), index=True, nullable=False)
    location_name = Column(String(150), index=True, nullable=False)
    surface_type = Column(String(30))
    is_active = Column(Boolean, default=True, index=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class DrawSlot(Base):
    __tablename__ = "draw_slots"
    id = Column(BigInteger, primary_key=True, index=True)
    tournament_id = Column(BigInteger, ForeignKey("tournaments.id"), index=True, nullable=False)
    slot_no = Column(Integer, index=True, nullable=False)
    bracket_position = Column(String(30), index=True, nullable=False)
    registration_id = Column(BigInteger, ForeignKey("registrations.id"), index=True)
    seed_no = Column(Integer)
    is_bye = Column(Boolean, default=False, index=True, nullable=False)
    slot_status = Column(String(20), index=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class Match(Base):
    __tablename__ = "matches"
    id = Column(BigInteger, primary_key=True, index=True)
    tournament_id = Column(BigInteger, ForeignKey("tournaments.id"), index=True, nullable=True)
    tournament_category_id = Column(BigInteger, ForeignKey("tournament_categories.id"), index=True, nullable=True) # Trận đấu thuộc nội dung nào
    stage_type = Column(String(20), index=True, nullable=False)
    group_id = Column(BigInteger, index=True) # ID ảo quản lý group, không fk cứng để dễ linh động
    round_code = Column(String(100), index=True, nullable=False)
    match_no = Column(Integer, index=True, nullable=False)
    side_a_registration_id = Column(BigInteger, ForeignKey("registrations.id"), index=True, nullable=True)
    side_b_registration_id = Column(BigInteger, ForeignKey("registrations.id"), index=True, nullable=True)
    winner_side = Column(String(20), nullable=True)
    winner_registration_id = Column(BigInteger, ForeignKey("registrations.id"), index=True)
    court_id = Column(BigInteger, ForeignKey("courts.id"), index=True)
    match_date = Column(Date, index=True)
    start_time = Column(DateTime, index=True)
    end_time = Column(DateTime)
    status = Column(String(20), index=True, nullable=False)
    score_summary = Column(String(255))
    result_note = Column(String(255))
    best_of_sets = Column(SmallInteger, nullable=False)
    ended_by = Column(BigInteger, ForeignKey("users.id"), index=True)
    updated_by = Column(BigInteger, ForeignKey("users.id"), index=True)
    next_match_id = Column(BigInteger, ForeignKey("matches.id"), index=True)
    live_stream_url = Column(String(500))
    video_url = Column(String(500)) # Video highlight hoặc full match
    image_url = Column(String(500)) # Hình ảnh nổi bật của trận
    win_reason = Column(String(50), index=True)
    elo_affected = Column(Boolean, default=True, index=True, nullable=False)
    referee_id = Column(BigInteger, ForeignKey("users.id"))
    referee_name = Column(String(100), nullable=True)
    referee_phone = Column(String(20), nullable=True)
    show_on_homepage = Column(Boolean, default=False, index=True, nullable=False)
    
    # Tỷ số trực tiếp theo Set (Phi chuẩn hóa)
    set1_a = Column(SmallInteger, nullable=True)
    set1_b = Column(SmallInteger, nullable=True)
    set2_a = Column(SmallInteger, nullable=True)
    set2_b = Column(SmallInteger, nullable=True)
    set3_a = Column(SmallInteger, nullable=True)
    set3_b = Column(SmallInteger, nullable=True)

    # Điểm Tie-break (nếu có)
    tie_break_1_a = Column(SmallInteger, nullable=True)
    tie_break_1_b = Column(SmallInteger, nullable=True)
    tie_break_2_a = Column(SmallInteger, nullable=True)
    tie_break_2_b = Column(SmallInteger, nullable=True)
    tie_break_3_a = Column(SmallInteger, nullable=True)
    tie_break_3_b = Column(SmallInteger, nullable=True)

    player_a_id = Column(Integer, ForeignKey("players.id"), nullable=True)
    player_b_id = Column(Integer, ForeignKey("players.id"), nullable=True)
    player_a2_id = Column(Integer, ForeignKey("players.id"), nullable=True)
    player_b2_id = Column(Integer, ForeignKey("players.id"), nullable=True)
    match_type = Column(String(30), default="singles", nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, index=True)

class MatchChallenge(Base):
    __tablename__ = "match_challenges"
    id = Column(BigInteger, primary_key=True, index=True)
    challenger_id = Column(BigInteger, ForeignKey("players.id"), nullable=False) # Người thách
    challenged_id = Column(BigInteger, ForeignKey("players.id"), nullable=False) # Người bị thách
    challenger_partner_id = Column(BigInteger, ForeignKey("players.id"), nullable=True) # Đồng đội người thách
    challenged_partner_id = Column(BigInteger, ForeignKey("players.id"), nullable=True) # Đồng đội người bị thách
    match_type = Column(String(30), default="singles", nullable=True)
    
    proposed_date = Column(Date, nullable=False) # Ngày dự kiến
    notes = Column(Text) # Lời nhắn (VD: 2 set cafe nhé)
    
    # Trạng thái: pending, accepted, rejected, waiting_payment, paid, scheduled, canceled
    status = Column(String(20), default="pending", index=True) 
    
    fee_amount = Column(Numeric(15, 2), default=200000) # Phí dịch vụ sân/trọng tài
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class MatchProgression(Base):
    __tablename__ = "match_progressions"
    id = Column(BigInteger, primary_key=True, index=True)
    from_match_id = Column(BigInteger, ForeignKey("matches.id"), index=True, nullable=False)
    to_match_id = Column(BigInteger, ForeignKey("matches.id"), index=True, nullable=False)
    target_side = Column(String(10), index=True, nullable=False)
    source_outcome = Column(String(10), index=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

# ==========================================
# MODULE 4: RANKING (Bảng xếp hạng)
# ==========================================

class Ranking(Base):
    __tablename__ = "rankings"
    id = Column(BigInteger, primary_key=True, index=True)
    ranking_target_type = Column(String(20), index=True, nullable=False)
    player_id = Column(BigInteger, ForeignKey("players.id"), index=True)
    team_id = Column(BigInteger, ForeignKey("teams.id"), index=True)
    category_type = Column(String(20), index=True, nullable=False)
    gender_division = Column(String(20), index=True, nullable=False)
    region_code = Column(String(50), index=True, nullable=False)
    rank_no = Column(Integer, index=True, nullable=False)
    elo_points = Column(Integer, index=True, nullable=False)
    matches_count = Column(Integer, default=0, nullable=False)
    wins_count = Column(Integer, default=0, nullable=False)
    losses_count = Column(Integer, default=0, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class RankingHistory(Base):
    __tablename__ = "ranking_history"
    id = Column(BigInteger, primary_key=True, index=True)
    ranking_target_type = Column(String(20), index=True, nullable=False)
    player_id = Column(BigInteger, ForeignKey("players.id"), index=True)
    team_id = Column(BigInteger, ForeignKey("teams.id"), index=True)
    match_id = Column(BigInteger, ForeignKey("matches.id"), index=True)
    category_type = Column(String(20), index=True, nullable=False)
    gender_division = Column(String(20), index=True, nullable=False)
    region_code = Column(String(50), index=True, nullable=False)
    points_before = Column(Integer, nullable=False)
    points_change = Column(Integer, nullable=False)
    points_after = Column(Integer, index=True, nullable=False)
    rank_before = Column(Integer)
    rank_after = Column(Integer)
    reason = Column(String(100), index=True, nullable=False)
    changed_by = Column(BigInteger, ForeignKey("users.id"), index=True)
    created_at = Column(DateTime, index=True, default=datetime.utcnow)

# ==========================================
# MODULE 1: CMS (Tin tức & Hình ảnh)
# ==========================================

class Category(Base):
    __tablename__ = "categories"
    id = Column(BigInteger, primary_key=True, index=True)
    name = Column(String(150), index=True, nullable=False)
    slug = Column(String(180), unique=True, nullable=False)
    type = Column(String(30), index=True, nullable=False)
    parent_id = Column(BigInteger, ForeignKey("categories.id"), index=True)
    sort_order = Column(Integer, nullable=False)
    is_active = Column(Boolean, default=True, index=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Post(Base):
    __tablename__ = "posts"
    id = Column(BigInteger, primary_key=True, index=True)
    title = Column(String(255), index=True, nullable=False)
    slug = Column(String(255), unique=True, nullable=False)
    summary = Column(Text)
    content = Column(Text)
    post_type = Column(String(30), index=True, nullable=False)
    category_id = Column(BigInteger, ForeignKey("categories.id"), index=True)
    author_id = Column(BigInteger, ForeignKey("users.id"), index=True, nullable=False)
    owner_user_id = Column(BigInteger, ForeignKey("users.id"), index=True)
    thumbnail_url = Column(String(500))
    media_url = Column(String(500))
    status = Column(String(20), index=True, nullable=False)
    publish_at = Column(DateTime, index=True)
    approved_by = Column(BigInteger, ForeignKey("users.id"), index=True)
    approved_at = Column(DateTime)
    rejected_reason = Column(String(255))
    published_by = Column(BigInteger, ForeignKey("users.id"), index=True)
    published_at = Column(DateTime, index=True)
    is_breaking_news = Column(Boolean, default=False, index=True, nullable=False)
    seo_title = Column(String(255))
    seo_description = Column(String(500))
    tags = Column(JSONB) # Dùng JSON lưu Array thay vì tạo bảng
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    category_rel = relationship("Category")
    
    @property
    def category(self):
        return self.category_rel.name if self.category_rel else "Chung"

class NewsletterSubscriber(Base):
    __tablename__ = "newsletter_subscribers"
    id = Column(BigInteger, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False)
    full_name = Column(String(150))
    is_active = Column(Boolean, default=True, index=True, nullable=False)
    subscribed_at = Column(DateTime, index=True, nullable=False)
    unsubscribed_at = Column(DateTime)
    source = Column(String(50))

class MediaAsset(Base):
    __tablename__ = "media_assets"
    id = Column(BigInteger, primary_key=True, index=True)
    entity_type = Column(String(30), index=True, nullable=False)
    entity_id = Column(BigInteger, index=True, nullable=False)
    file_type = Column(String(30), index=True, nullable=False)
    file_url = Column(String(500), unique=True, nullable=False)
    file_name = Column(String(255), nullable=False)
    file_size = Column(BigInteger)
    mime_type = Column(String(120))
    created_at = Column(DateTime, default=datetime.utcnow)

# ==========================================
# MODULE 6: ADMIN & SYSTEM LOGS (Nhật ký)
# ==========================================

class ActivityLog(Base):
    __tablename__ = "activity_logs"
    id = Column(BigInteger, primary_key=True, index=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), index=True)
    module_name = Column(String(50), index=True, nullable=False)
    action_type = Column(String(30), index=True, nullable=False)
    entity_type = Column(String(50), index=True, nullable=False)
    entity_id = Column(BigInteger, index=True)
    old_data_json = Column(Text)
    new_data_json = Column(Text)
    ip_address = Column(String(50))
    event_name = Column(String(100))
    is_processed = Column(Boolean, default=False, index=True, nullable=False)
    processed_at = Column(DateTime, index=True)
    created_at = Column(DateTime, index=True, default=datetime.utcnow)

class WebhookLog(Base):
    __tablename__ = "webhook_logs"
    id = Column(BigInteger, primary_key=True, index=True)
    source = Column(String(50), index=True, nullable=False)
    event_type = Column(String(100), index=True, nullable=False)
    reference_code = Column(String(100), index=True)
    payload_json = Column(JSONB, nullable=False)
    headers_json = Column(JSONB)
    signature = Column(String(255))
    processing_status = Column(String(20), index=True, nullable=False)
    processed_at = Column(DateTime, index=True)
    notes = Column(String(255))
    created_at = Column(DateTime, index=True, default=datetime.utcnow)

class Setting(Base):
    __tablename__ = "settings"
    id = Column(BigInteger, primary_key=True, index=True)
    setting_key = Column(String(100), unique=True, nullable=False)
    setting_group = Column(String(50), index=True, nullable=False)
    setting_value = Column(Text)
    data_type = Column(String(30), index=True, nullable=False)
    is_secret = Column(Boolean, default=False, index=True, nullable=False)
    description = Column(String(255))
    updated_by = Column(BigInteger, ForeignKey("users.id"), index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# ==========================================
# MODULE 7: COMMUNICATION & CHAT (Tương tác)
# ==========================================

# ==========================================
# MODULE 6.5: MARKETING (Banner & Sponsors)
# ==========================================

class MarketingBanner(Base):
    __tablename__ = "marketing_banners"
    id = Column(BigInteger, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    subtitle = Column(String(255))
    image_url = Column(String(500), nullable=False)
    link_url = Column(String(500))
    placement = Column(String(50), index=True, nullable=False, default="home_top")
    display_order = Column(Integer, default=0, index=True, nullable=False)
    is_active = Column(Boolean, default=True, index=True, nullable=False)
    open_in_new_tab = Column(Boolean, default=True, nullable=False)
    start_at = Column(DateTime, index=True)
    end_at = Column(DateTime, index=True)
    created_by = Column(BigInteger, ForeignKey("users.id"), index=True)
    updated_by = Column(BigInteger, ForeignKey("users.id"), index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

class Sponsor(Base):
    __tablename__ = "sponsors"
    id = Column(BigInteger, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    logo_url = Column(String(500), nullable=False)
    website_url = Column(String(500))
    tier = Column(String(50), index=True, nullable=False, default="partner")
    description = Column(Text)
    display_order = Column(Integer, default=0, index=True, nullable=False)
    is_active = Column(Boolean, default=True, index=True, nullable=False)
    start_at = Column(DateTime, index=True)
    end_at = Column(DateTime, index=True)
    created_by = Column(BigInteger, ForeignKey("users.id"), index=True)
    updated_by = Column(BigInteger, ForeignKey("users.id"), index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

class Notification(Base):
    __tablename__ = "notifications"
    id = Column(BigInteger, primary_key=True, index=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), index=True, nullable=False)
    type = Column(String(20), index=True, nullable=False)
    channel = Column(String(20), index=True, nullable=False)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    related_entity_type = Column(String(50), index=True)
    related_entity_id = Column(BigInteger, index=True)
    is_sent = Column(Boolean, default=False, index=True, nullable=False)
    delivery_status = Column(String(20), index=True, nullable=False)
    websocket_session_id = Column(String(255), index=True)
    sent_at = Column(DateTime, index=True)
    read_at = Column(DateTime, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class ChatRoom(Base):
    __tablename__ = "chat_rooms"
    id = Column(BigInteger, primary_key=True, index=True)
    name = Column(String(150), index=True)
    type = Column(String(20), index=True, nullable=False) # PUBLIC, PRIVATE
    created_at = Column(DateTime, default=datetime.utcnow)

class ChatParticipant(Base):
    __tablename__ = "chat_participants"
    id = Column(BigInteger, primary_key=True, index=True)
    room_id = Column(BigInteger, ForeignKey("chat_rooms.id"), nullable=False)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    joined_at = Column(DateTime, default=datetime.utcnow)

class ChatMessage(Base):
    __tablename__ = "chat_messages"
    id = Column(BigInteger, primary_key=True, index=True)
    room_id = Column(BigInteger, ForeignKey("chat_rooms.id"), nullable=False)
    sender_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    content = Column(Text, nullable=False)
    message_type = Column(String(20), nullable=False)
    is_read = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, index=True, default=datetime.utcnow)

class MailCampaign(Base):
    __tablename__ = "mail_campaigns"
    
    id = Column(BigInteger, primary_key=True, index=True)
    tournament_id = Column(BigInteger, ForeignKey("tournaments.id"), nullable=False)
    subject = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    total_recipients = Column(Integer, default=0)
    sent_at = Column(DateTime, default=datetime.utcnow)
    scheduled_at = Column(DateTime, nullable=True) # Thời gian dự kiến gửi (Nếu Null là gửi ngay)
    status = Column(String(20), default="pending", index=True) # Trạng thái: pending, sent, failed
