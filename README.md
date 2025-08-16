# 校园点歌系统后端

本项目是校园点歌系统的FastAPI后端服务，实现了微信小程序登录、用户绑定、歌曲搜索、点歌、管理员审核、歌曲播放等全流程功能，集成网易云音乐播放直链获取。

## 技术栈

- **Web框架**: FastAPI
- **ORM**: SQLAlchemy
- **数据库**: PostgreSQL
- **身份验证**: JWT
- **API集成**: 网易云音乐API

## 项目结构

```
ourapp_back/
├── app/                        # 应用主目录
│   ├── api/                    # API路由模块
│   │   ├── admin.py           # 管理员相关API
│   │   ├── player.py          # 播放器相关API
│   │   ├── songs.py           # 歌曲搜索API
│   │   └── wechat.py          # 微信小程序相关API
│   ├── core/                   # 核心配置
│   │   ├── config.py          # 应用配置
│   │   └── security.py        # 安全相关工具
│   ├── db/                     # 数据库相关
│   │   ├── models/            # 数据模型
│   │   ├── repositories/      # 数据访问层
│   │   └── session.py         # 数据库会话
│   ├── schemas/               # 请求/响应模式
│   ├── services/              # 业务逻辑服务
│   └── main.py                # 应用入口
├── cookie.txt                  # 网易云音乐cookie
├── database.db                 # SQLite数据库文件
├── requirements.txt            # 依赖包列表
├── migrate.py                  # 数据库迁移脚本
└── run.py                      # 启动脚本
```

## 功能模块

### 微信小程序模块
- **登录**: 通过微信小程序code换取openid并生成JWT令牌
- **绑定**: 将微信用户与学生信息绑定
- **刷新令牌**: 支持访问令牌过期后使用刷新令牌获取新令牌
- **点歌**: 用户提交点歌请求

### 管理员模块
- **登录**: 管理员账号密码登录
- **歌曲审核**: 查看和审核点歌请求
- **数据管理**: 管理用户和歌曲数据

### 播放器模块
- **队列管理**: 获取待播放歌曲队列
- **状态更新**: 标记歌曲播放状态

### 音乐服务
- **歌曲搜索**: 搜索网易云音乐歌曲
- **获取直链**: 获取歌曲播放地址
- **获取歌词**: 获取歌曲歌词

## 快速开始

### 1. 环境准备

确保已安装Python 3.8+和pip。

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置环境变量

在项目根目录创建`.env`文件：

``` dotenv
# JWT配置
JWT_SECRET=your_secure_jwt_secret_key

# 微信小程序配置
WECHAT_APPID=your_wechat_appid
WECHAT_SECRET=your_wechat_secret

# 数据库配置（如使用PostgreSQL）
POSTGRES_USER=postgres
POSTGRES_PASSWORD=yourpassword
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=your-database-name
```

### 4. 初始化数据库

使用以下命令初始化数据库：

```bash
# 导入初始数据
python migrate.py
```

默认管理员账号：
- 用户名: su
- 密码: XxshSU0081

### 5. 启动服务

```bash
# 使用run.py启动
python run.py

# 或使用uvicorn直接启动
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

服务启动后，可访问 http://localhost:8000/docs 查看API文档。

## API接口说明

## 目录

- [微信小程序相关接口](#微信小程序相关接口)
- [管理员接口](#管理员接口)
- [播放器接口](#播放器接口)
- [歌曲搜索与数据获取接口](#歌曲搜索与数据获取接口)

## 微信小程序相关接口

### 微信登录

**请求**:
- 方法: `POST`
- 路径: `/api/wechat/login`
- 内容类型: `application/json`

**请求体**:
```json
{
  "code": "string"  // 微信小程序登录返回的code
}
```

**响应**:
```json
{
  "access_token": "string",
  "refresh_token": "string",
  "token_type": "bearer"
}
```

**描述**: 使用微信小程序获取的code进行登录，返回JWT访问令牌和刷新令牌。

---

### 微信账号绑定

**请求**:
- 方法: `POST`
- 路径: `/api/wechat/bind`
- 内容类型: `application/json`
- 授权: Bearer Token

**请求体**:
```json
{
  "student_id": "string",  // 学生ID
  "name": "string"         // 学生姓名
}
```

**响应**:
```json
{
  "success": true,
  "msg": "绑定成功"
}
```

**描述**: 将微信账号与学生信息绑定。学生ID和姓名必须正确匹配，且一个学生ID只能绑定一个微信账号。

---

### 刷新令牌

**请求**:
- 方法: `POST`
- 路径: `/api/wechat/refresh`
- 内容类型: `application/json`

**请求体**:
```json
{
  "refresh_token": "string"  // 刷新令牌
}
```

**响应**:
```json
{
  "access_token": "string",
  "refresh_token": "string",
  "token_type": "bearer"
}
```

**描述**: 使用刷新令牌获取新的访问令牌和刷新令牌。

---

### 检查是否已绑定

**请求**:
- 方法: `GET`
- 路径: `/api/wechat/isbound`
- 授权: Bearer Token

**响应**:
```json
{
  "is_bound": true  // 或 false
}
```

**描述**: 检查当前微信账号是否已经绑定到学生账号。

---

### 点歌请求

**请求**:
- 方法: `POST`
- 路径: `/api/wechat/song/request`
- 内容类型: `application/json`
- 授权: Bearer Token

**请求体**:
```json
{
  "song_id": "string"  // 网易云音乐歌曲ID
}
```

**响应**:
```json
{
  "success": true,
  "msg": "点歌成功，等待审核"
}
```

**描述**: 提交点歌请求。系统有以下限制：
- 普通用户在30分钟内只能点一次歌
- 不能重复点同一首歌
- 普通用户最多有3首未审核/未播放的歌曲

## 管理员接口

### 管理员登录

**请求**:
- 方法: `POST`
- 路径: `/api/admin/login`
- 内容类型: `application/json`

**请求体**:
```json
{
  "username": "string",
  "password": "string"
}
```

**响应**:
```json
{
  "access_token": "string",
  "token_type": "bearer"
}
```

**描述**: 管理员登录，返回JWT访问令牌。

---

### 获取歌曲请求列表

**请求**:
- 方法: `GET`
- 路径: `/api/admin/song/list`
- 参数: `status` - 歌曲状态，如 "pending"、"approved"、"rejected"、"played"
- 授权: Bearer Token (管理员)

**响应**:
```json
{
  "songs": [
    {
      "id": "integer",
      "song_id": "string",
      "song_name": "string",
      "artist": "string",
      "requester_name": "string",
      "requester_id": "string",
      "status": "string",
      "request_time": "string",
      "review_time": "string",
      "reviewer_name": "string",
      "reason": "string"
    }
  ]
}
```

**描述**: 获取指定状态的歌曲请求列表。

---

### 审核歌曲请求

**请求**:
- 方法: `POST`
- 路径: `/api/admin/song/review`
- 内容类型: `application/json`
- 授权: Bearer Token (管理员)

**请求体**:
```json
{
  "song_request_id": "integer",  // 歌曲请求ID
  "status": "string",            // "approved" 或 "rejected"
  "reason": "string"             // 拒绝理由，可选
}
```

**响应**:
```json
{
  "success": true,
  "msg": "审核成功"
}
```

**描述**: 管理员审核歌曲请求，可以批准或拒绝。只能审核状态为"pending"的请求。

## 播放器接口

### 获取播放队列

**请求**:
- 方法: `GET`
- 路径: `/api/player/queue`

**响应**:
```json
{
  "queue": [
    {
      "id": "integer",
      "song_id": "string",
      "song_name": "string",
      "artist": "string",
      "requester_name": "string",
      "requester_id": "string",
      "status": "approved",
      "request_time": "string",
      "review_time": "string",
      "reviewer_name": "string"
    }
  ]
}
```

**描述**: 获取已审核批准但尚未播放的歌曲队列。

---

### 标记歌曲已播放

**请求**:
- 方法: `POST`
- 路径: `/api/player/played`
- 内容类型: `application/json`

**请求体**:
```json
{
  "request_id": "integer"  // 歌曲请求ID
}
```

**响应**:
```json
{
  "success": true
}
```

**描述**: 将歌曲标记为已播放状态。

## 歌曲搜索与数据获取接口

### 搜索歌曲

**请求**:
- 方法: `GET`
- 路径: `/api/search`
- 参数:
  - `query`: 搜索关键词（必填）
  - `source`: 音乐源（可选）
  - `count`: 返回结果数量，默认30
  - `page`: 页码，默认1

**响应**:
```json
{
  "songs": [
    {
      "id": "string",
      "name": "string",
      "artist": "string",
      "album": "string",
      "pic_url": "string",
      "source": "string"
    }
  ]
}
```

**描述**: 通过GDstudio API搜索歌曲。

---

### 获取歌曲播放链接

**请求**:
- 方法: `GET`
- 路径: `/api/geturl`
- 参数:
  - `id`: 歌曲ID（必填）
  - `source`: 音乐源（可选）
  - `br`: 比特率（可选）

**响应**:
```json
{
  "url": "string",
  "br": "integer",
  "size": "integer",
  "md5": "string",
  "type": "string"
}
```

**描述**: 获取指定歌曲的播放直链。

---

### 获取歌词

**请求**:
- 方法: `GET`
- 路径: `/api/getlyric`
- 参数:
  - `id`: 歌曲ID（必填）
  - `source`: 音乐源（可选）

**响应**:
```json
{
  "lyric": "string",
  "tlyric": "string"
}
```

**描述**: 获取指定歌曲的歌词和翻译歌词（如果有）。
