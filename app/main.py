from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import wechat, songs, player, wall
from app.core.config import settings
from app.db.session import engine
from app.db.models import User, SongRequest, RefreshToken, WallMessage

# 创建FastAPI应用实例
app = FastAPI(title="校园点歌系统API",
    description="实现了微信小程序端的登录、绑定、搜索、点歌、管理员审核、歌曲播放等全流程",
    version="1.0.0")

# 配置CORS
origins = [
    'http://localhost:5173',
    # 其他允许的前端域名
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(wechat.router, prefix=f"{settings.API_V1_STR}/wechat", tags=["微信小程序"])
app.include_router(songs.router, prefix=settings.API_V1_STR, tags=["歌曲搜索"])
app.include_router(player.router, prefix=f"{settings.API_V1_STR}/player", tags=["播放器"])
app.include_router(wall.router, prefix=f"{settings.API_V1_STR}/wall", tags=["校园墙"])

@app.get("/",description="API根路径", summary="API根路径",
         responses={
                200: {
                    "description": "欢迎信息",
                    "content": {
                        "application/json": {
                            "example": {"message": "Welcome to Song Request System API"}
                        }
                    }
                }
         })
def read_root():
    return {"message": "Welcome to Song Request System API"}
