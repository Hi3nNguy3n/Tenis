# backend/app/crud/crud_post.py
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.models.models import Post, Category
from app.schemas.post_schemas import PostCreate, PostUpdate
from app.core.text import slugify

def get_post(db: Session, post_id: int):
    return db.query(Post).filter(Post.id == post_id).first()

def get_post_by_slug(db: Session, slug: str):
    return db.query(Post).filter(Post.slug == slug).first()

from app.models.models import Post, Category # Nhớ import Category

def get_posts(db: Session, skip: int = 0, limit: int = 100, search: str = None, category: str = None):
    # Dùng outerjoin để kết nối bảng Post và Category
    query = db.query(Post).outerjoin(Category, Post.category_id == Category.id)
    
    if search:
        query = query.filter(Post.title.ilike(f"%{search}%"))
        
    if category and category != 'Tất cả':
        # Lọc dựa trên tên của bảng Category
        query = query.filter(Category.name == category)
        
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

    # 3. XỬ LÝ DANH MỤC: Đổi 'Chữ' thành 'ID'
    category_name = post.category or "Thông báo"
    category_obj = db.query(Category).filter(Category.name == category_name).first()
    
    # Nếu danh mục chưa có, tự động tạo mới KÈM THEO SLUG
    if not category_obj:
        cat_slug = slugify(category_name) # Tạo slug cho danh mục
        category_obj = Category(name=category_name, slug=cat_slug, type="news", sort_order=1) # Thêm slug vào đây
        db.add(category_obj)
        db.commit()
        db.refresh(category_obj)

    # 4. Chuẩn bị dữ liệu: LOẠI BỎ thêm 'post_type' ra khỏi dict để không bị trùng
    post_data = post.model_dump(exclude={"category", "category_id", "post_type"}) 
    
    db_post = Post(
        **post_data,
        category_id=category_obj.id, 
        slug=unique_slug,
        author_id=author_id,
        owner_user_id=author_id,
        post_type="news"  # Bây giờ gán cứng ở đây sẽ an toàn tuyệt đối
    )
    
    # 5. Lưu vào DB
    try:
        db.add(db_post)
        db.commit()
        db.refresh(db_post)
        return db_post
    except Exception as e:
        db.rollback() 
        raise e

def update_post(db: Session, db_post: Post, post_in: PostUpdate):
    # Lấy dữ liệu update, LOẠI BỎ cột 'category' (chữ)
    update_data = post_in.model_dump(exclude_unset=True, exclude={"category"})
    
    # Nếu đổi tiêu đề, cập nhật lại slug
    if "title" in update_data and update_data["title"] != db_post.title:
        base_slug = slugify(update_data["title"])
        unique_slug = base_slug
        counter = 1
        while db.query(Post).filter(Post.slug == unique_slug, Post.id != db_post.id).first():
            unique_slug = f"{base_slug}-{counter}"
            counter += 1
        update_data["slug"] = unique_slug

    # XỬ LÝ DANH MỤC (Nếu Frontend có gửi category mới)
    if post_in.category:
        category_obj = db.query(Category).filter(Category.name == post_in.category).first()
        if not category_obj:
            cat_slug = slugify(post_in.category) # Tạo slug cho danh mục
            category_obj = Category(name=post_in.category, slug=cat_slug, type="news", sort_order=1) # Thêm slug vào đây
            db.add(category_obj)
            db.commit()
            db.refresh(category_obj)
            
        update_data["category_id"] = category_obj.id

    for field, value in update_data.items():
        setattr(db_post, field, value)

    db.commit()
    db.refresh(db_post)
    return db_post

def delete_post(db: Session, db_post: Post):
    db.delete(db_post)
    db.commit()
    return db_post