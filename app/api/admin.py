from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Dict, Any
from sqlalchemy.orm import Session

from app.schemas.auth import AdminLoginRequest
from app.schemas.song import SongReviewRequest
from app.services.auth import verify_admin_login
from app.db.repositories import song_request_repository
from app.core.security import get_admin_id
from app.db.session import get_db

router = APIRouter()

@router.post("/login",
             summary="管理员登录",
             responses={
                 200: {
                        "description": "登录成功，返回管理员信息和访问令牌",
                        "content": {
                            "application/json": {
                                "example": {
                                    "admin_id": 1,
                                    "username": "admin",
                                    "token": "your_access_token"
                                }
                            }
                        }
                 },
                 401:{
                        "description": "用户名或密码错误",
                        "content": {
                            "application/json": {
                                "example": {"detail": "用户名或密码错误"}
                            }
                        }
                 }
             }
             )
def admin_login(
    data: AdminLoginRequest, 
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    管理员登录接口
    """
    result = verify_admin_login(data.username, data.password, db)
    
    if not result:
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    
    return result

@router.get("/song/list",
            summary="管理员获取歌曲请求列表",
            responses={
                200: {
                    "description": "成功返回歌曲请求列表",
                    "content": {
                        "application/json": {
                            "example": {
                                "songs": [
                                    {
                                        "id": 1,
                                        "song_id": 123,
                                        "song_name": "ber",
                                        "status": "pending",
                                        "request_time": "2023-10-01T12:00:00Z",
                                        "review_time": None,
                                        "review_reason": None,
                                        "student_id": 456,
                                        "name": "张三",
                                        "wechat_openid": "openid123"
                                    }
                                ]
                            }
                        }
                    }
                },
                400: {
                    "description": "状态参数错误",
                    "content": {
                        "application/json": {
                            "example": {"detail": "status参数错误"}
                        }
                    }
                }
            }
            )
def admin_song_list(
    status: str = Query(...), 
    db: Session = Depends(get_db),
    admin_id: int = Depends(get_admin_id)
) -> Dict[str, Any]:
    songs = song_request_repository.get_song_requests_by_status(db, status)
    return {"songs": songs}

@router.post("/song/review",
             summary="管理员审核歌曲请求",
                responses={
                    200: {
                        "description": "审核成功",
                        "content": {
                            "application/json": {
                                "example": {"success": True, "msg": "审核成功"}
                            }
                        }
                    },
                    400: {
                        "description": "请求参数错误或点歌记录不存在",
                        "content": {
                            "application/json": {
                                "example": {"detail": "status只能为approved或rejected"}
                            }
                        }
                    },
                    404: {
                        "description": "点歌记录不存在",
                        "content": {
                            "application/json": {
                                "example": {"detail": "点歌记录不存在"}
                            }
                        }
                    }
                }
             )
def admin_song_review(
    data: SongReviewRequest, 
    db: Session = Depends(get_db),
    admin_id: int = Depends(get_admin_id)
) -> Dict[str, Any]:
    if data.status not in ("approved", "rejected"):
        raise HTTPException(status_code=400, detail="status只能为approved或rejected")
    
    current_status = song_request_repository.get_song_request_status(db, data.song_request_id)
    
    if not current_status:
        raise HTTPException(status_code=404, detail="点歌记录不存在")
    
    if current_status != "pending":
        raise HTTPException(status_code=400, detail="该点歌已审核过")
    
    song_request_repository.update_song_request_status(
        db, data.song_request_id, data.status, data.reason, admin_id
    )
    
    return {"success": True, "msg": "审核成功"}