from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.db.models.song_request import SongRequest
from app.db.models.user import User
from app.schemas.song import SongRequest as SongRequestSchema, SongRequestResponse
from app.db.repositories.base import BaseRepository

class SongRequestRepository(BaseRepository[SongRequest, SongRequestSchema, SongRequestSchema]):
    """歌曲请求数据访问层"""
    
    def check_recent_song_requests(self, db: Session, user_id: int, minutes: int = 30) -> int:
        """检查用户最近的点歌请求"""
        thirty_min_ago = datetime.now() - timedelta(minutes=minutes)
        return db.query(SongRequest).filter(
            SongRequest.user_id == user_id,
            SongRequest.request_time > thirty_min_ago,
            SongRequest.status.in_(["pending", "approved", "played"])
        ).count()
    
    def check_song_already_requested(self, db: Session, user_id: int, song_id: str) -> bool:
        """检查用户是否已经请求过该歌曲"""
        return db.query(SongRequest).filter(
            SongRequest.song_id == song_id,
            SongRequest.status.in_(["pending", "approved"])
        ).count() > 0
    
    def count_pending_approved_songs(self, db: Session, user_id: int) -> int:
        """计算用户待审核和已批准的歌曲数量"""
        return db.query(SongRequest).filter(
            SongRequest.user_id == user_id,
            SongRequest.status.in_(["pending", "approved"])
        ).count()
    
    def create_song_request(self, db: Session, user_id: int, song_id: str,song_name:str) -> SongRequest:
        """创建歌曲请求"""
        song_request = SongRequest(
            user_id=user_id,
            song_id=song_id,
            song_name=song_name,
            status="pending",
            request_time=datetime.now()
        )
        db.add(song_request)
        db.commit()
        db.refresh(song_request)
        return song_request
    
    def get_song_requests_by_status(self, db: Session, status: str) -> List[Dict[str, Any]]:
        """获取指定状态的歌曲请求列表"""
        query = db.query(
            SongRequest.id,
            SongRequest.song_id,
            SongRequest.song_name,
            SongRequest.status,
            SongRequest.request_time,
            SongRequest.review_time,
            SongRequest.review_reason,
            User.student_id,
            User.name,
            User.wechat_openid
        ).join(
            User, User.id == SongRequest.user_id
        ).filter(
            SongRequest.status == status
        ).order_by(
            SongRequest.request_time.asc()
        )
        
        result = []
        for row in query.all():
            # 转换查询结果为字典
            result.append({
                "id": row.id,
                "song_id": row.song_id,
                "song_name": row.song_name,
                "status": row.status,
                "request_time": row.request_time,
                "review_time": row.review_time,
                "review_reason": row.review_reason,
                "student_id": row.student_id,
                "name": row.name,
                "wechat_openid": row.wechat_openid
            })
        
        return result
    
    def get_song_request_status(self, db: Session, request_id: int) -> Optional[str]:
        """获取歌曲请求的状态"""
        request = db.query(SongRequest).filter(SongRequest.id == request_id).first()
        return request.status if request else None# type: ignore
    
    def update_song_request_status(
        self, db: Session, request_id: int, status: str, reason: str = "", reviewer_id: int|None = None
    ) -> SongRequest:
        """更新歌曲请求的状态"""
        request = db.query(SongRequest).filter(SongRequest.id == request_id).first()
        if request:
            request.status = status# type: ignore
            request.review_time = datetime.now()# type: ignore
            request.review_reason = reason# type: ignore
            request.reviewer_id = reviewer_id# type: ignore
            db.commit()
            db.refresh(request)
        return request
    
    def get_approved_song_queue(self, db: Session) -> List[Dict[str, Any]]:
        """获取已批准的歌曲队列"""
        query = db.query(SongRequest.id, SongRequest.song_id).filter(
            SongRequest.status == "approved"
        ).order_by(
            SongRequest.request_time.asc()
        )
        
        result = []
        for row in query.all():
            result.append({
                "request_id": row.id,
                "song_id": row.song_id
            })
        
        return result
    def get_requests_by_user_id(self, db: Session, user_id: int,status:List[str]) -> List[SongRequest]:
        """根据ID获取歌曲请求"""
        fetchall = db.query(SongRequest).filter(SongRequest.user_id == user_id, SongRequest.status.in_(status)).all()
        result = []
        for row in fetchall:
            result.append(SongRequestResponse.model_validate(row))
        return result

# 实例化仓库
song_request_repository = SongRequestRepository(SongRequest)