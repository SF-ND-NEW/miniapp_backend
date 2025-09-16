from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

from app.schemas.base import BaseSchema

# 请求模式
class UserCreate(BaseModel):
    student_id: str
    name: str

class UserUpdate(BaseModel):
    wechat_openid: Optional[str] = None
    name: Optional[str] = None

class UserBind(BaseModel):
    student_id: str
    name: str

# 响应模式
class UserResponse(BaseSchema):
    id: int
    student_id: str
    name: str
    wechat_openid: Optional[str] = None
    bind_time: Optional[datetime] = None
    is_admin: bool = False