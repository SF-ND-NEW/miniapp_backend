from typing import Optional, Tuple
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import Column, String

from app.db.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.db.repositories.base import BaseRepository

class UserRepository(BaseRepository[User, UserCreate, UserUpdate]):
    """用户数据访问层"""
    
    def get_by_openid(self, db: Session, openid: str) -> Optional[User]:
        """通过微信openid获取用户"""
        return db.query(User).filter(User.wechat_openid == openid).first()
    
    def get_by_student_id_and_name(self, db: Session, student_id: str, name: str) -> Optional[User]:
        """通过学号和姓名获取用户"""
        return db.query(User).filter(
            User.student_id == student_id,
            User.name == name
        ).first()
    
    def bind_user(self, db: Session, user_id: int, openid: str) -> User:
        """绑定用户的微信openid"""
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            user.wechat_openid = openid  # type: ignore
            user.bind_time = datetime.now()  # type: ignore
            db.commit()
            db.refresh(user)
        return user

# 实例化仓库
user_repository = UserRepository(User)