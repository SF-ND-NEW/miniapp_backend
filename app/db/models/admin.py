from sqlalchemy import Column, String

from app.db.session import Base
from app.db.models.base import BaseModel

class Admin(BaseModel):
    """管理员模型"""
    __tablename__ = "admins"
    
    username = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    
    def __repr__(self):
        return f"<Admin {self.username}>"