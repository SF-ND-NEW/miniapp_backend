from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.repositories.user import user_repository
from app.schemas.user import UserResponse
from app.core.security import get_openid

router = APIRouter()


@router.get("/me",
            response_model=UserResponse,
            summary="获取当前用户信息",
            description="获取当前登录用户的详细信息")
def get_current_user_info(
    db: Session = Depends(get_db),
    openid: str = Depends(get_openid)
):
    """获取当前用户信息"""
    user = user_repository.get_by_openid(db, openid)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    return UserResponse.from_orm(user)