from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any
from sqlalchemy.orm import Session

from app.schemas.song import PlayerPlayedRequest, CurrentSongResponse
from app.db.repositories import song_request_repository
from app.db.session import get_db
from app.core.security import require_admin

router = APIRouter()

@router.get("/current",
            summary="获取当前播放歌曲",
            description="获取当前正在播放的歌曲信息和播放状态")
def get_current_song(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """获取当前播放的歌曲"""
    current_song_data = song_request_repository.get_current_playing_song(db)
    
    is_playing = current_song_data is not None
    
    return {
        "current_song": current_song_data,
        "is_playing": is_playing,
        "queue_position": 1 if current_song_data else None
    }

@router.get("/queue",summary="获取歌曲队列",description="获取已批准的歌曲队列",
            responses={
                200: {
                    "description": "成功返回歌曲队列",
                    "content": {
                        "application/json": {
                            "example": {
                                "queue": [
                                    {
                                        "id": 123,
                                        "title": "Example Song",
                                        "artist": "Artist Name",
                                        "requester_name": "用户名",
                                        "created_at": "2024-01-01T00:00:00"
                                    }
                                ]
                            }
                        }
                    }
                },
                404: {
                    "description": "没有找到已批准的歌曲队列",
                    "content": {
                        "application/json": {
                            "example": {"detail": "没有找到已批准的歌曲队列"}
                        }
                    }
                }
            })
def player_queue(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    获取已批准的歌曲队列
    """
    songs = song_request_repository.get_approved_song_queue(db)
    return {"queue": songs}

@router.post("/played",description="标记歌曲已播放",summary="标记歌曲为已播放",
             responses={
                    200: {
                        "description": "成功标记歌曲为已播放",
                        "content": {
                            "application/json": {
                                "example": {"success": True}
                            }
                        }
                    },
                    404: {
                        "description": "请求ID无效或歌曲未找到",
                        "content": {
                            "application/json": {
                                "example": {"detail": "请求ID无效或歌曲未找到"}
                            }
                        }
                    }
             })
def player_played(
    data: PlayerPlayedRequest, 
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    标记歌曲为已播放
    """
    song_request_repository.update_song_request_status(db, data.request_id, "played")
    return {"success": True}