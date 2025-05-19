import sqlite3

from fastapi import FastAPI, HTTPException, Header, Depends, Query, Body
from dotenv import load_dotenv
from pydantic import BaseModel
import jwt
import datetime
from werkzeug.security import check_password_hash
from fastapi.middleware.cors import CORSMiddleware
import os
import json
import urllib.parse
from hashlib import md5
from random import randrange
import requests
from fastapi import APIRouter, Query
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

app = FastAPI()
load_dotenv()
JWT_SECRET = os.getenv("JWT_SECRET")
WECHAT_APPID = os.getenv("WECHAT_APPID")
WECHAT_SECRET = os.getenv("WECHAT_SECRET")
origins = [
    'http://localhost:5173',
    'http://localhost:8000'
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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


class AdminLoginRequest(BaseModel):
    username: str
    password: str

def get_admin_by_username(username):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, password_hash FROM admin WHERE username=?", (username,))
    row = cursor.fetchone()
    conn.close()
    return row

@app.post("/api/admin/login")
def admin_login(data: AdminLoginRequest):
    row = get_admin_by_username(data.username)
    if not row:
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    admin_id, password_hash = row
    if not check_password_hash(password_hash, data.password):
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    payload = {
        "admin_id": admin_id,
        "username": data.username,
        "exp": datetime.datetime.now() + datetime.timedelta(hours=8)
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")
    if isinstance(token, bytes):
        token = token.decode('utf-8')
    return {"token": token, "username": data.username}

def get_admin_id(authorization: str = Header(...)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="认证信息缺失或格式错误")
    token = authorization.split(" ")[1]
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
    except Exception:
        raise HTTPException(status_code=401, detail="token无效或已过期")
    return payload["admin_id"]

@app.get("/api/admin/song/list")
def admin_song_list(status: str = Query(...), admin_id: int = Depends(get_admin_id)):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute('''
        SELECT sr.id, sr.song_id, sr.status, sr.request_time, sr.review_time, sr.review_reason, 
               u.student_id, u.name, u.wechat_openid
          FROM song_request sr
          JOIN user u ON sr.user_id = u.id
         WHERE sr.status = ?
         ORDER BY sr.request_time ASC
    ''', (status,))
    rows = cursor.fetchall()
    conn.close()
    song_list = []
    for row in rows:
        song_list.append({
            "id": row[0],
            "song_id": row[1],
            "status": row[2],
            "request_time": row[3],
            "review_time": row[4],
            "review_reason": row[5],
            "student_id": row[6],
            "name": row[7],
            "wechat_openid": row[8],
        })
    return {"songs": song_list}

class SongReviewRequest(BaseModel):
    song_request_id: int
    status: str  # 'approved' or 'rejected'
    reason: str = ""

@app.post("/api/admin/song/review")
def admin_song_review(data: SongReviewRequest, admin_id: int = Depends(get_admin_id)):
    if data.status not in ("approved", "rejected"):
        raise HTTPException(status_code=400, detail="status只能为approved或rejected")
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT status FROM song_request WHERE id=?", (data.song_request_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="点歌记录不存在")
    if row[0] != "pending":
        conn.close()
        raise HTTPException(status_code=400, detail="该点歌已审核过")
    cursor.execute('''
        UPDATE song_request SET status=?, review_time=?, review_reason=?, reviewer_id=?
        WHERE id=?
    ''', (data.status, datetime.datetime.now(), data.reason, admin_id, data.song_request_id))
    conn.commit()
    conn.close()
    return {"success": True, "msg": "审核成功"}


@app.get("/api/player/queue")
def api_player_queue():
    # 返回状态为“approved”的未播放歌曲，按时间排序
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, song_id FROM song_request WHERE status = 'approved' ORDER BY request_time ASC"
    )
    songs = [{"request_id": row[0], "song_id": row[1]} for row in cursor.fetchall()]
    conn.close()
    return {"queue": songs}

class PlayerPlayedRequest(BaseModel):
    request_id: int
@app.post("/api/player/played")
def api_player_played(data: PlayerPlayedRequest):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE song_request SET status='played', review_time=? WHERE id=?",
        (datetime.datetime.now(), data.request_id)
    )
    conn.commit()
    conn.close()
    return {"success": True}


# --- 工具函数 ---
def HexDigest(data):
    return "".join([hex(d)[2:].zfill(2) for d in data])


def HashDigest(text):
    return md5(text.encode("utf-8")).digest()


def HashHexDigest(text):
    return HexDigest(HashDigest(text))


def parse_cookie(text: str):
    cookie_ = [item.strip().split('=', 1) for item in text.strip().split(';') if item]
    cookie_ = {k.strip(): v.strip() for k, v in cookie_}
    return cookie_


def read_cookie():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    cookie_file = os.path.join(script_dir, 'cookie.txt')
    with open(cookie_file, 'r') as f:
        cookie_contents = f.read()
    return cookie_contents


def post(url, params, cookie):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Safari/537.36 Chrome/91.0.4472.164 NeteaseMusicDesktop/2.10.2.200154',
        'Referer': '',
    }
    cookies = {
        "os": "pc",
        "appver": "",
        "osver": "",
        "deviceId": "pyncm!"
    }
    cookies.update(cookie)
    response = requests.post(url, headers=headers, cookies=cookies, data={"params": params})
    return response.text


def url_v1(id, level, cookies):
    url = "https://interface3.music.163.com/eapi/song/enhance/player/url/v1"
    AES_KEY = b"e82ckenh8dichen8"
    config = {
        "os": "pc",
        "appver": "",
        "osver": "",
        "deviceId": "pyncm!",
        "requestId": str(randrange(20000000, 30000000))
    }

    payload = {
        'ids': [id],
        'level': level,
        'encodeType': 'flac',
        'header': json.dumps(config),
    }

    if level == 'sky':
        payload['immerseType'] = 'c51'

    url2 = urllib.parse.urlparse(url).path.replace("/eapi/", "/api/")
    digest = HashHexDigest(f"nobody{url2}use{json.dumps(payload)}md5forencrypt")
    params = f"{url2}-36cd479b6b5-{json.dumps(payload)}-36cd479b6b5-{digest}"
    padder = padding.PKCS7(algorithms.AES(AES_KEY).block_size).padder()
    padded_data = padder.update(params.encode()) + padder.finalize()
    cipher = Cipher(algorithms.AES(AES_KEY), modes.ECB())
    encryptor = cipher.encryptor()
    enc = encryptor.update(padded_data) + encryptor.finalize()
    params = HexDigest(enc)
    response = post(url, params, cookies)
    return json.loads(response)


def get_res(id):
    cookies = parse_cookie(read_cookie())
    res = url_v1(id, "standard", cookies)
    return res


@app.get("/api/geturl")
def api_geturl(id: str = Query(..., description="网易云音乐歌曲ID")):
    """
    获取网易云音乐播放直链
    """
    response = get_res(id)
    res = {
        "code": response.get("code", -1),
        "data": response["data"][0] if "data" in response and len(response["data"]) > 0 else {}
    }
    return res