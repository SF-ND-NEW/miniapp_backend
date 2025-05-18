# 点歌台后端（FastAPI + SQLite）

本项目是为学生会运动会点歌小程序设计的后端，支持小程序点歌、树莓派放歌与后台审核三端对接，使用 Python 的 FastAPI 框架与 SQLite 数据库实现。

---

## 目录

- [功能简介](#功能简介)
- [数据库结构](#数据库结构)
- [API 文档](#api-文档)
  - [小程序 API](#小程序-api)
  - [管理员后台 API](#管理员后台-api)
  - [树莓派端 API](#树莓派端-api)
- [快速启动](#快速启动)
- [部署指南（DigitalOcean）](#部署指南digitalocean)
- [安全建议](#安全建议)
- [后续可拓展点](#后续可拓展点)

---

## 功能简介

- **学生微信小程序端**：绑定学号，点歌，查询点歌历史
- **管理员后台**：登录，歌曲请求审核，查询历史
- **树莓派放歌端**：拉取待播放歌曲，标记已播放

---

## 数据库结构

### 1. User（用户表）

| 字段名           | 类型       | 说明         |
|------------------|----------|--------------|
| id               | INTEGER  | 主键，自增   |
| wechat_openid    | TEXT     | 微信openid，唯一|
| student_id       | INTEGER  | 学号         |
| name             | TEXT     | 姓名         |
| bind_time        | DATETIME | 绑定时间     |

### 2. SongRequest（点歌请求表）

| 字段名           | 类型      | 说明         |
|------------------|-----------|--------------|
| id               | INTEGER   | 主键，自增   |
| user_id          | INTEGER   | 外键，用户ID |
| song_id          | INTEGER   | 歌曲ID（整数）|
| status           | TEXT      | 状态：`pending`（待审核），`approved`（通过），`rejected`（驳回），`played`（已播放）|
| request_time     | DATETIME  | 请求时间     |
| review_time      | DATETIME  | 审核时间     |
| admin_id         | INTEGER   | 外键，管理员ID（可为空）|

### 3. Admin（管理员表）

| 字段名           | 类型      | 说明         |
|------------------|-----------|--------------|
| id               | INTEGER   | 主键，自增   |
| username         | TEXT      | 用户名，唯一 |
| password_hash    | TEXT      | 密码哈希     |

---

## API 文档

所有接口均为 RESTful 风格，采用 JSON 作为传递格式。

### 小程序 API

前缀：`/api/wechat`

#### 1. 绑定微信和学号

- **POST** `/api/wechat/bind`
- **Body:**
  ```json
  {
    "wechat_openid": "openid_xxx",
    "student_id": "20250001",
    "name": "张三"
  }
  ```
- **返回:**
  ```json
  {
    "success": true,
    "msg": "绑定成功"
  }
  ```

#### 2. 点歌请求

- **POST** `/api/wechat/song/request`
- **Body:**
  ```json
  {
    "wechat_openid": "openid_xxx",
    "song_id": 12345
  }
  ```
- **返回:**
  ```json
  {
    "success": true,
    "msg": "请求成功，等待审核"
  }
  ```

#### 3. 查询点歌历史

- **GET** `/api/wechat/song/history?wechat_openid=openid_xxx`
- **返回:**
  ```json
  {
    "history": [
      {
        "song_request_id": 1,
        "song_id": 12345,
        "status": "approved",
        "request_time": "2025-05-16 15:00"
      }
    ]
  }
  ```

---

### 管理员后台 API

前缀：`/api/admin`

#### 1. 管理员登录

- **POST** `/api/admin/login`
- **Body:**
  ```json
  {
    "username": "admin",
    "password": "yourpassword"
  }
  ```
- **返回:**
  ```json
  {
    "token": "jwt_token_xxx"
  }
  ```

#### 2. 查询点歌请求

- **GET** `/api/admin/song/list?status=pending`
- **Header:** `Authorization: Bearer <token>`
- **返回:**
  ```json
  {
    "requests": [
      {
        "song_request_id": 1,
        "song_id": 12345,
        "user": {"student_id": "20250001", "name": "张三"},
        "status": "pending",
        "request_time": "2025-05-16 15:00"
      }
    ]
  }
  ```

#### 3. 审核/更改歌曲状态

- **POST** `/api/admin/song/review`
- **Header:** `Authorization: Bearer <token>`
- **Body:**
  ```json
  {
    "song_request_id": 1,
    "status": "approved"
  }
  ```
- **返回:**
  ```json
  {
    "success": true,
    "msg": "审核成功"
  }
  ```

---

### 树莓派端 API

前缀：`/api/pi`

#### 1. 获取下一首可播放歌曲

- **GET** `/api/pi/song/next`
- **返回:**
  ```json
  {
    "song_request_id": 1,
    "song_id": 12345
  }
  ```

#### 2. 标记已播放

- **POST** `/api/pi/song/played`
- **Body:**
  ```json
  {
    "song_request_id": 1
  }
  ```
- **返回:**
  ```json
  {
    "success": true,
    "msg": "已标记为已播放"
  }
  ```

---

## 快速启动

1. **克隆代码并安装依赖**
    ```bash
    git clone https://github.com/yourusername/song-request-backend.git
    cd song-request-backend
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    ```

2. **初始化数据库**
    - 首次运行时，FastAPI 项目会自动创建 SQLite 数据库和表。
    - 或运行自带的初始化脚本（如有）。

3. **启动服务**
    ```bash
    uvicorn main:app --host 0.0.0.0 --port 8000
    ```

4. **访问接口**
    - 小程序/前端/树莓派通过 RESTful API 调用后端
    - 管理员可用 Postman 或前端页面调用管理端接口

---

## 安全

- 管理员密码需加密存储（建议 bcrypt）
- 所有管理端接口需强认证（JWT/Session）
- 避免明文存储敏感信息
- 生产环境请定期备份 SQLite 数据库
- 控制 API 访问频率防刷

---


如需详细开发文档、接口示例代码，或有定制化需求请联系开发者。