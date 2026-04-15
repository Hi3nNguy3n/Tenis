# backend/app/crud/crud_post.py
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.models.models import Post
from app.schemas.post_schemas import PostCreate, PostUpdate
from app.core.text import slugify

def get_post(db: Session, post_id: int):
    return db.query(Post).filter(Post.id == post_id).first()

def get_post_by_slug(db: Session, slug: str):
    return db.query(Post).filter(Post.slug == slug).first()

def get_posts(db: Session, skip: int = 0, limit: int = 100, search: str = None, category: str = None):
    query = db.query(Post)
    
    if search:
        query = query.filter(Post.title.ilike(f"%{search}%"))
    # Nếu category là String (Tên danh mục), bạn sẽ cần Join bảng Categories. 
    # Nhưng hiện tại category đang truyền vào là ID hoặc xử lý mảng
    
    # Sắp xếp bài mới nhất lên đầu
    return query.order_by(Post.created_at.desc()).offset(skip).limit(limit).all()

def create_post(db: Session, post: PostCreate, author_id: int):
    # 1. Tạo Base Slug từ Tiêu đề
    base_slug = slugify(post.title)
    unique_slug = base_slug
    
    # 2. Xử lý trùng lặp Slug
    counter = 1
    while db.query(Post).filter(Post.slug == unique_slug).first():
        unique_slug = f"{base_slug}-{counter}"
        counter += 1

    # 3. Chuẩn bị dữ liệu (BỎ exclude_unset=True)
    # Sử dụng model_dump() bình thường để lấy cả các giá trị default (như post_type="news")
    post_data = post.model_dump() 
    
    db_post = Post(
        **post_data,
        slug=unique_slug,
        author_id=author_id,
        owner_user_id=author_id
    )
    
    # 4. Lưu vào DB
    try:
        db.add(db_post)
        db.commit()
        db.refresh(db_post)
        return db_post
    except Exception as e:
        db.rollback() # Luôn rollback nếu lỗi để tránh treo session
        raise e

def update_post(db: Session, db_post: Post, post_in: PostUpdate):
    update_data = post_in.model_dump(exclude_unset=True)
    
    # Nếu đổi tiêu đề, cập nhật lại slug
    if "title" in update_data and update_data["title"] != db_post.title:
        base_slug = slugify(update_data["title"])
        unique_slug = base_slug
        counter = 1
        while db.query(Post).filter(Post.slug == unique_slug, Post.id != db_post.id).first():
            unique_slug = f"{base_slug}-{counter}"
            counter += 1
        update_data["slug"] = unique_slug

    for field, value in update_data.items():
        setattr(db_post, field, value)

    db.commit()
    db.refresh(db_post)
    return db_post

def delete_post(db: Session, db_post: Post):
    db.delete(db_post)
    db.commit()
    return db_post