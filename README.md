# 校园点歌系统 · 后端服务 & 使用说明

本项目为校园点歌系统的 FastAPI 后端，实现了微信小程序端的登录、绑定、搜索、点歌、管理员审核、歌曲播放等全流程，集成网易云音乐播放直链获取能力，适合部署至树莓派等设备实现自动播放。

---

## 目录结构

- `main.py` —— 主后端服务，所有API接口实现
- `cookie.txt` —— 网易云音乐网页版cookie（用于获取播放直链，需手动获取）
- `database.db` —— SQLite数据库
- `requirements.txt` —— 依赖包列表

---

## 主要功能

- **微信小程序端相关**
  - `/api/wechat/login` 微信登录，返回小程序JWT
  - `/api/wechat/bind` 绑定学号与微信号
  - `/api/wechat/isbound` 查询是否已绑定
  - `/api/search` 网易云歌曲搜索
  - `/api/wechat/song/request` 发起点歌请求

- **管理员后台**
  - `/api/admin/login` 管理员登录
  - `/api/admin/song/list` 查询指定状态的点歌请求（如：待审核）
  - `/api/admin/song/review` 审核点歌（通过/驳回）

- **播放与播放器**
  - `/api/player/queue` 获取待播放歌曲队列
  - `/api/player/played` 标记某个点歌已播放

- **网易云音乐直链**
  - `/api/geturl?id=xxx` 获取指定网易云歌曲ID的播放直链（需配合有效cookie.txt）

---

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
# 或手动安装
pip install fastapi uvicorn pydantic python-dotenv werkzeug cryptography requests
```

### 2. 准备数据库

首次运行时会自动创建表并初始化测试用户（学号：271837，姓名：郑光朔）和管理员（用户名/密码：admin）。

### 3. 获取网易云 cookie

- 登录网页版网易云音乐，F12 控制台获取你的 cookie，复制粘贴到 `cookie.txt` 文件（同 main.py 同级目录）。
- 示例内容（使用你自己的）：
  ```
  MUSIC_U=xxx; __csrf=xxx; ...  # 一行
  ```

### 4. 配置环境变量

在项目目录下新建 `.env` 文件（用于微信小程序登录）：

```
JWT_SECRET=your_jwt_secret_key
WECHAT_APPID=your_wx_appid
WECHAT_SECRET=your_wx_secret
```

### 5. 启动后端服务

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 6. 主要API速查

- **小程序端**
  - 登录：`POST /api/wechat/login`  body: `{ code }`
  - 绑定：`POST /api/wechat/bind`  headers: `Authorization: Bearer <token>`
  - 搜索：`GET /api/search?query=xxx`
  - 点歌：`POST /api/wechat/song/request`  headers: `Authorization: Bearer <token>`

- **管理员**
  - 登录：`POST /api/admin/login`  body: `{ username, password }`
  - 审核列表：`GET /api/admin/song/list?status=pending`  headers: `Authorization: Bearer <token>`
  - 审核操作：`POST /api/admin/song/review`  headers: `Authorization: Bearer <token>`

- **播放器**
  - 获取队列：`GET /api/player/queue`
  - 标记已播：`POST /api/player/played`  body: `{ request_id }`
  - 获取直链：`GET /api/geturl?id=xxx`  返回网易云可播放URL

---

## 树莓派/本地播放器推荐流程

1. 定时轮询 `/api/player/queue` 获取下一个 approved 歌曲
2. 调用 `/api/geturl?id=xxx` 获取播放地址
3. 用 `python-vlc`、`mpg123` 等库播放（支持流式）
4. 播放完成后调用 `/api/player/played` 标记已播

---

## 常见问题

### Q: 网易云直链为何获取失败？
- 检查 cookie.txt 是否最新、有效（避免登录失效）
- 网易云部分歌曲版权原因可能无外链

### Q: 数据库如何自定义初始化？
- 参见 `main.py` 末尾建表和测试数据部分，自行增删

### Q: 小程序端如何对接？
- 所有接口均为标准 RESTful，参考微信小程序 fetch/request 用法

---

## 安全提示

- 管理员接口建议生产环境加更严格鉴权
- 切勿泄露 cookie.txt、.env 等敏感信息至公有仓库

---

## 贡献

如有建议、Bug或功能需求，欢迎提Issue或PR。

---

## License

MIT