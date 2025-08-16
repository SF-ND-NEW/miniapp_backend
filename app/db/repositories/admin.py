from typing import Optional, Tuple
from sqlalchemy.orm import Session

from app.db.models.admin import Admin
from app.schemas.auth import AdminLoginRequest
from app.db.repositories.base import BaseRepository

class AdminRepository(BaseRepository[Admin, AdminLoginRequest, AdminLoginRequest]):
    """管理员数据访问层"""
    
    def get_by_username(self, db: Session, username: str) -> Optional[Admin]:
        """通过用户名获取管理员"""
        return db.query(Admin).filter(Admin.username == username).first()

# 实例化仓库
admin_repository = AdminRepository(Admin)