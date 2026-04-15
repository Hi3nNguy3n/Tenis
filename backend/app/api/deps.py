# backend/app/api/deps.py
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.crud import crud_auth
from app.core.config import settings
from app.models.models import User

security = HTTPBearer()

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Không thể xác thực thông tin (Token không hợp lệ hoặc hết hạn).",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        token = credentials.credentials 
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
        
    user = crud_auth.get_user_by_id(db, user_id=int(user_id))
    
    if user is None:
        raise credentials_exception
    
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Tài khoản người dùng đã bị khóa.")
        
    return user

def get_current_admin(
    current_user: User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    role = crud_auth.get_role_by_id(db, role_id=current_user.role_id)
    if not role or role.role_key != "admin":
        raise HTTPException(
            status_code=403, 
            detail="Truy cập bị từ chối. Chỉ Quản trị viên mới được thực hiện hành động này."
        )
    return current_user