# backend/app/api/news.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.db.database import get_db
from app.models.models import User
# Hàm lấy user này lấy từ hệ thống Auth của bạn
from app.api.deps import get_current_user, get_current_admin 
from app.schemas.post_schemas import PostCreate, PostUpdate, PostResponse
from app.crud import crud_post
from app.core.audit import audit_log # Nếu bạn đang dùng hệ thống ghi Log

router = APIRouter()

@router.get("", response_model=List[PostResponse], include_in_schema=False)
@router.get("/", response_model=List[PostResponse])
def read_posts(
    skip: int = 0, 
    limit: int = 100, 
    search: Optional[str] = None,
    category: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Lấy danh sách tin tức. (Hỗ trợ lọc theo từ khóa và danh mục)
    """
    posts = crud_post.get_posts(db, skip=skip, limit=limit, search=search, category=category)
    return posts

@router.post("", response_model=PostResponse, include_in_schema=False)
@router.post("/", response_model=PostResponse)
@audit_log(module="NEWS", action="CREATE", event_name="Đăng bài viết mới")
def create_post(
    post_in: PostCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin) # Chỉ Admin mới được đăng bài
):
    """
    Đăng bài viết mới (Dành cho Admin).
    """
    return crud_post.create_post(db=db, post=post_in, author_id=current_user.id)

@router.get("/{slug_or_id}", response_model=PostResponse)
def read_post(slug_or_id: str, db: Session = Depends(get_db)):
    """
    Lấy thông tin chi tiết bài viết qua ID hoặc Slug.
    """
    # Thử tìm theo ID trước, nếu không được thì tìm theo Slug
    if slug_or_id.isdigit():
        post = crud_post.get_post(db, post_id=int(slug_or_id))
    else:
        post = crud_post.get_post_by_slug(db, slug=slug_or_id)
        
    if not post:
        raise HTTPException(status_code=404, detail="Bài viết không tồn tại")
    return post

@router.put("/{post_id}", response_model=PostResponse)
@audit_log(module="NEWS", action="UPDATE", event_name="Cập nhật bài viết")
def update_post(
    post_id: int,
    post_in: PostUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Cập nhật bài viết.
    """
    post = crud_post.get_post(db, post_id=post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Bài viết không tồn tại")
    
    return crud_post.update_post(db=db, db_post=post, post_in=post_in)

@router.delete("/{post_id}")
@audit_log(module="NEWS", action="DELETE", event_name="Xóa bài viết")
def delete_post(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Xóa bài viết.
    """
    post = crud_post.get_post(db, post_id=post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Bài viết không tồn tại")
    
    crud_post.delete_post(db=db, db_post=post)
    return {"message": "Đã xóa bài viết thành công"}
