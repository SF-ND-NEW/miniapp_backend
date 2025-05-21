from sqlite3 import connect
from werkzeug.security import generate_password_hash
conn = connect('database.db')
cursor = conn.cursor()
cursor.execute('PRAGMA foreign_keys = ON;')
conn.commit()
'''
| 字段名           | 类型       | 说明         |
|------------------|----------|--------------|
| id               | INTEGER  | 主键，自增   |
| wechat_openid    | TEXT     | 微信openid，唯一|
| student_id       | INTEGER  | 学号         |
| name             | TEXT     | 姓名         |
| bind_time        | DATETIME | 绑定时间     |
'''
# 创建表
cursor.execute(
    '''
    CREATE TABLE IF NOT EXISTS user (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        wechat_openid TEXT UNIQUE,
        student_id INTEGER UNIQUE,
        name TEXT NOT NULL,
        bind_time DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    '''
)


'''
| 字段名           | 类型      | 说明         |
|------------------|-----------|--------------|
| id               | INTEGER   | 主键，自增   |
| username         | TEXT      | 用户名，唯一 |
| password_hash    | TEXT      | 密码哈希     |
'''
cursor.execute('''
    CREATE TABLE IF NOT EXISTS admin(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL 
    )
''')


'''
| 字段名           | 类型      | 说明         |
|------------------|-----------|--------------|
| id               | INTEGER   | 主键，自增   |
| user_id          | INTEGER   | 外键，用户ID |
| song_id          | INTEGER   | 歌曲ID（整数）|
| status           | TEXT      | 状态：`pending`（待审核），`approved`（通过），`rejected`（驳回），`played`（已播放）|
| request_time     | DATETIME  | 请求时间     |
| review_time      | DATETIME  | 审核时间     |
| review_reason   | TEXT      | 审核理由（可为空）|
| reviewer_id     | INTEGER   | 外键，审核人ID（可为空）|
'''
cursor.execute('''
    CREATE TABLE IF NOT EXISTS song_request(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        song_id INTEGER NOT NULL,
        status TEXT CHECK(status IN ('pending', 'approved', 'rejected', 'played')),
        request_time DATETIME DEFAULT CURRENT_TIMESTAMP,
        review_time DATETIME,
        review_reason TEXT,
        reviewer_id INTEGER,
        FOREIGN KEY(user_id) REFERENCES user(id)
    )
''')
# test：初始化测试数据 User 114514
cursor.execute('''
    SELECT wechat_openid FROM user WHERE student_id=271837
''')
row = cursor.fetchone()
if not row:
    cursor.execute('''
        INSERT INTO user (wechat_openid, student_id, name)
        VALUES (null, 114514, 'User')
    ''')
    conn.commit()
else:
    cursor.execute('''
        UPDATE user SET wechat_openid=null WHERE student_id=114514
    ''')
    conn.commit()
# test: 初始化测试数据 admin admin
cursor.execute('''
    SELECT username FROM admin WHERE username='admin'
''')
row = cursor.fetchone()
password_hash = generate_password_hash('admin')
if not row:
    cursor.execute('''
        INSERT INTO admin (username, password_hash)
        VALUES ('admin', ?)
    ''', (password_hash,))
    conn.commit()
else:
    cursor.execute('''
        UPDATE admin SET password_hash=? WHERE username='admin'
    ''', (password_hash,))
    conn.commit()
# 提交更改并关闭连接
conn.commit()
conn.close()
