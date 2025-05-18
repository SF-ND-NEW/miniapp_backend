import sqlite3

from fastapi import FastAPI, HTTPException, Header, Depends, Query
from dotenv import load_dotenv
import os
import requests
from pydantic import BaseModel
import jwt
import datetime


app = FastAPI()
load_dotenv()
JWT_SECRET = os.getenv("JWT_SECRET")
WECHAT_APPID = os.getenv("WECHAT_APPID")
WECHAT_SECRET = os.getenv("WECHAT_SECRET")


def create_jwt_token(openid: str):
    """
    创建JWT token
    :param openid: 微信用户的openid
    :return: JWT token
    """
    payload = {
        "openid": openid,
        "exp": datetime.datetime.now() + datetime.timedelta(days=7)# 过期时间设置为7天
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")
    return token


def get_openid(authorization: str = Header(...)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="认证信息缺失或格式错误")
    token = authorization.split(" ")[1]
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
    except Exception:
        raise HTTPException(status_code=401, detail="token无效或已过期")
    return payload["openid"]


class LoginRequest(BaseModel):
    code:str
@app.post("/api/wechat/login")
def login_wechat(data: LoginRequest):
    """
    微信登录接口
    :param data: 包含微信返回的code
    :return: 登录结果
    """
    wx_url = (
        "https://api.weixin.qq.com/sns/jscode2session?"
        f"appid={WECHAT_APPID}&secret={WECHAT_SECRET}"
        f"&js_code={data.code}&grant_type=authorization_code"
    )
    resp = requests.get(wx_url)
    wx_data = resp.json()
    if "errcode" in wx_data and wx_data["errcode"] != 0:
        raise HTTPException(status_code=400, detail=f"微信登录失败: {wx_data.get('errmsg')}")
    openid = wx_data["openid"]
    jwt_token = create_jwt_token(openid)
    return {"token": jwt_token}


class BindRequest(BaseModel):
    student_id: str
    name: str


@app.post("/api/wechat/bind")
def wechat_bind(data: BindRequest, openid: str = Depends(get_openid)):
    """
    绑定微信账号和学号
    :param data: 包含学号和姓名
    :param openid: 微信用户的openid
    :return: 绑定结果
    """
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    # 检查是否有此学号与姓名
    cursor.execute("SELECT id, wechat_openid FROM user WHERE student_id=? AND name=?", (data.student_id, data.name))
    row = cursor.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=400, detail="学号或姓名不正确")
    user_id, old_openid = row
    # 检查是否已绑定
    if old_openid and old_openid != openid:
        conn.close()
        raise HTTPException(status_code=400, detail="该学号已被其他微信绑定")
    if old_openid == openid:
        conn.close()
        return {"success": True, "msg": "曾经已绑定过"}
    # 绑定openid
    cursor.execute("UPDATE user SET wechat_openid=?, bind_time=? WHERE id=?",
                   (openid, datetime.datetime.now(), user_id))
    conn.commit()
    conn.close()
    return {"success": True, "msg": "绑定成功"}


@app.get("/api/wechat/isbound")
def is_bound(openid: str = Depends(get_openid)):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM user WHERE wechat_openid=?", (openid,))
    row = cursor.fetchone()
    conn.close()
    return {"is_bound": bool(row)}


@app.get("/api/search")
def api_search(query: str = Query(..., min_length=1)):
    url = "https://music.163.com/api/search/get/web"
    params = {
        "csrf_token": "",
        "hlpretag": "",
        "hlposttag": "",
        "s": query,
        "type": 1,
        "offset": 0,
        "total": "true",
        "limit": 30
    }
    try:
        resp = requests.get(url, params=params, timeout=4)
        data = resp.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail="网易云接口请求失败:"+str(e))
    # 提取简要信息返回
    songs = []
    for song in data.get("result", {}).get("songs", []):
        songs.append({
            "id": song["id"],
            "name": song["name"],
            "artists": [a["name"] for a in song["artists"]],
            "album": song["album"]["name"] if song.get("album") else "",
            "duration": song["duration"],
            "cover": song["album"]["picId"] if song.get("album") else None
        })
    return {"songs": songs}

class SongRequest(BaseModel):
    song_id: int
@app.post("/api/wechat/song/request")
def song_request(data:SongRequest, openid: str = Depends(get_openid)):
    song_id = data.song_id
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    # 获取user_id
    cursor.execute("SELECT id FROM user WHERE wechat_openid=?", (openid,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=400, detail="未绑定用户")
    user_id = row[0]

    # 1. 30分钟内是否点过歌
    thirty_min_ago = datetime.datetime.now() - datetime.timedelta(minutes=30)
    cursor.execute(
        "SELECT COUNT(*) FROM song_request WHERE user_id=? AND request_time>? AND status IN ('pending','approved','played')",
        (user_id, thirty_min_ago)
    )
    count_30min = cursor.fetchone()[0]
    if count_30min > 0:
        conn.close()
        raise HTTPException(status_code=400, detail="30分钟内只能点一次歌，请稍后再试")

    # 2. 是否点过该歌曲（未驳回的都算）
    cursor.execute(
        "SELECT COUNT(*) FROM song_request WHERE user_id=? AND song_id=? AND status IN ('pending','approved','played')",
        (user_id, song_id)
    )
    already = cursor.fetchone()[0]
    if already > 0:
        conn.close()
        raise HTTPException(status_code=400, detail="你已经点过这首歌了")

    # 3. 是否超出3首未完成
    cursor.execute(
        "SELECT COUNT(*) FROM song_request WHERE user_id=? AND status IN ('pending','approved')",
        (user_id,)
    )
    ing = cursor.fetchone()[0]
    if ing >= 3:
        conn.close()
        raise HTTPException(status_code=400, detail="你最多只能有3首未审核通过或未播放的歌曲")

    # 插入点歌请求
    cursor.execute(
        "INSERT INTO song_request (user_id, song_id, status, request_time) VALUES (?, ?, ?, ?)",
        (user_id, song_id, "pending", datetime.datetime.now())
    )
    conn.commit()
    conn.close()
    return {"success": True, "msg": "点歌成功，等待审核"}