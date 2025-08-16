from datetime import datetime
from typing import Optional
from pydantic import BaseModel as PydanticBaseModel

class BaseSchema(PydanticBaseModel):
    """所有Pydantic模型的基础类"""
    class Config:
        from_attributes = True  # 启用ORM模式，可直接从SQLAlchemy模型创建