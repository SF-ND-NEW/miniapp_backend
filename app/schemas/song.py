from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel

from app.schemas.base import BaseSchema

# API请求模式
class SongRequest(BaseModel):
    song_id: str
    song_name: str;

class SongReviewRequest(BaseModel):
    song_request_id: int
    status: str  # 'approved' or 'rejected'
    reason: str = ""

class PlayerPlayedRequest(BaseModel):
    request_id: int

# API响应模式
class Song(BaseModel):
    id: str
    name: str
    artists: List[str]
    album: str
    duration: Optional[int] = None
    cover: Optional[str] = None

class SearchResponse(BaseModel):
    songs: List[Song]

class SongRequestResponse(BaseSchema):
    id: int
    song_id: str
    song_name: str
    status: str
    request_time: datetime
    review_time: Optional[datetime] = None
    review_reason: Optional[str] = None
    user_id: int
    user_name: Optional[str] = None
    user_student_id: Optional[str] = None