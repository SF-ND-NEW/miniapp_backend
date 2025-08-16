import jwt
from fastapi import HTTPException, Header, Depends
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db

def get_openid(authorization: str = Header(...), db: Session = Depends(get_db)) -> str:
    """
    从JWT令牌中获取openid
    """
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="认证信息缺失或格式错误")
    
    token = authorization.split(" ")[1]
    
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])
        
        # 确保这是访问令牌而不是刷新令牌
        if payload.get("type") == "refresh":
            raise HTTPException(status_code=401, detail="无效的令牌类型")
            
        return payload["openid"]
    except jwt.ExpiredSignatureError:
        # 当令牌过期时，返回特殊的状态码，前端可以捕获并尝试刷新
        raise HTTPException(status_code=401, detail="token已过期，请刷新")
    except Exception:
        raise HTTPException(status_code=401, detail="token无效")

def get_admin_id(authorization: str = Header(...)) -> int:
    """
    从JWT令牌中获取admin_id
    """
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="认证信息缺失或格式错误")
    
    token = authorization.split(" ")[1]
    
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])
    except Exception:
        raise HTTPException(status_code=401, detail="token无效或已过期")
    
    return payload["admin_id"]