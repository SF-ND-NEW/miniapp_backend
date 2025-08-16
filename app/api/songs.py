from fastapi import APIRouter, Query
from typing import Dict, Any, List

from app.schemas.song import Song
from app.services.music_api import music_api_service

router = APIRouter()

@router.get("/search",
            response_model=Dict[str, List[Song]],
            summary="歌曲搜索",
            description="进行歌曲搜索",
            responses={
                200: {
                    "description": "成功返回歌曲列表",
                    "content": {
                        "application/json": {
                            "example": {
                                "songs": [
                                    {
                                        "id": "123456",
                                        "name": "Example Song",
                                        "artists": ["Artist Name"],
                                        "album": "Example Album",
                                        "duration": 240,
                                        "cover": "http://example.com/cover.jpg",
                                        "source": "netease"
                                    }
                                ]
                            }
                        }
                    }
                },
                400: {
                    "description": "查询参数错误",
                    "content": {
                        "application/json": {
                            "example": {"detail": "查询参数错误"}
                        }
                    }
                }
            }
            )

def search_songs(query: str = Query(..., min_length=1), 
                 source: str|None = None, 
                 count: int = 30, 
                 page: int = 1) -> Dict[str, List[Song]]:
    songs = music_api_service.search_songs(query, source, count, page)
    return {"songs": songs}

@router.get("/geturl",summary="获取歌曲URL",description="获取歌曲的播放URL",
            responses={
                200: {
                    "description": "成功返回歌曲URL",
                    "content": {
                        "application/json": {
                            "example": {
                                "url": "http://example.com/song.mp3",
                                "source": "netease",
                                "br": "320k"
                            }
                        }
                    }
                },
                400: {
                    "description": "查询参数错误",
                    "content": {
                        "application/json": {
                            "example": {"detail": "查询参数错误"}
                        }
                    }
                }
            })
def get_song_url(id: str = Query(..., description="Song ID"), 
                 source: str|None = None,
                 br: str|None = None) -> Dict[str, Any]:
    return music_api_service.get_song_url(id, source, br)
