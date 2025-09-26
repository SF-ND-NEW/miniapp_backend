import sqlite3
import datetime
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
import argparse

# 加载环境变量
load_dotenv()

# PostgreSQL连接配置
PG_USER = os.getenv("POSTGRES_USER", "postgres")
PG_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")
PG_HOST = os.getenv("POSTGRES_HOST", "localhost")
PG_PORT = os.getenv("POSTGRES_PORT", "5432")
PG_DB = os.getenv("POSTGRES_DB", "miniapp")

# SQLite数据库文件
SQLITE_DB = "database.db"

def create_postgres_tables(delete_existing: bool):
    """创建PostgreSQL数据库表"""
    print(f"连接到PostgreSQL数据库: {PG_DB} at {PG_HOST}:{PG_PORT} as user {PG_USER}")
    conn = psycopg2.connect(
        dbname=PG_DB,
        user=PG_USER,
        password=PG_PASSWORD,
        host=PG_HOST,
        port=PG_PORT
    )
    cursor = conn.cursor()

    # 删除已经创建的表
    if delete_existing:
        cursor.execute("DROP TABLE IF EXISTS users CASCADE")
        cursor.execute("DROP TABLE IF EXISTS song_requests CASCADE")
        cursor.execute("DROP TABLE IF EXISTS refresh_tokens CASCADE")
        cursor.execute("DROP TABLE IF EXISTS wall_messages CASCADE")
        cursor.execute("DROP TABLE IF EXISTS comments CASCADE")
        conn.commit()
    
    # 创建users表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            wechat_openid VARCHAR(50) UNIQUE,
            student_id VARCHAR(10) UNIQUE NOT NULL,
            name VARCHAR(50) NOT NULL,
            bind_time TIMESTAMP,
            is_admin BOOLEAN NOT NULL DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    
    # 创建song_requests表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS song_requests (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            song_id VARCHAR(50) NOT NULL,
            song_name VARCHAR(500) NOT NULL,
            status VARCHAR(10) NOT NULL CHECK (status IN ('pending', 'approved', 'rejected', 'played')),
            request_time TIMESTAMP NOT NULL,
            review_time TIMESTAMP,
            review_reason TEXT,
            reviewer_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)
    
    # 创建refresh_tokens表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS refresh_tokens (
            id SERIAL PRIMARY KEY,
            openid VARCHAR(50) NOT NULL,
            token_id VARCHAR(50) NOT NULL,
            expires_at TIMESTAMP NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(openid, token_id)
        )
    """)
    
    # 创建wall_messages表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS wall_messages (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            title VARCHAR(200),
            content TEXT NOT NULL,
            message_type VARCHAR(20) NOT NULL CHECK (message_type IN ('general', 'lost_and_found', 'confession', 'help', 'announcement')) DEFAULT 'general',
            status VARCHAR(20) NOT NULL CHECK (status IN ('PENDING', 'APPROVED', 'REJECTED', 'DELETED')) DEFAULT 'PENDING',
            contact_info VARCHAR(200),
            location VARCHAR(200),
            files VARCHAR(500),
            tags VARCHAR(500),
            view_count INTEGER NOT NULL DEFAULT 0,
            like_count INTEGER NOT NULL DEFAULT 0,
            timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # 创建comments表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS comments (
            id SERIAL PRIMARY KEY,
            wall_id INTEGER NOT NULL, 
            user_id INTEGER NOT NULL,
            content TEXT NOT NULL,
            status VARCHAR(20) NOT NULL CHECK (status IN ('PENDING', 'APPROVED', 'REJECTED', 'DELETED')) DEFAULT 'PENDING',
            like_count INTEGER NOT NULL DEFAULT 0,
            timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (wall_id) REFERENCES wall_messages(id)
        )
    """)
    
    # 创建索引
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_openid ON users(wechat_openid)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_student_id ON users(student_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_song_requests_user_id ON song_requests(user_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_song_requests_status ON song_requests(status)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_refresh_tokens_openid ON refresh_tokens(openid)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_refresh_tokens_token_id ON refresh_tokens(token_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_wall_messages_user_id ON wall_messages(user_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_wall_messages_status ON wall_messages(status)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_wall_messages_type ON wall_messages(message_type)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_wall_messages_timestamp ON wall_messages(timestamp)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_wall_messages_like_count ON wall_messages(like_count)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_wall_messages_view_count ON wall_messages(view_count)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_comments_user_id ON comments(user_id)");
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_comments_like_count ON comments(like_count)");

    # 提交更改并关闭连接
    conn.commit()
    conn.close()
    
    print("PostgreSQL数据库表创建成功")

def migrate_users():
    """迁移用户数据"""
    # 连接SQLite数据库
    sqlite_conn = sqlite3.connect(SQLITE_DB)
    sqlite_conn.row_factory = sqlite3.Row
    sqlite_cursor = sqlite_conn.cursor()
    
    # 获取所有用户
    sqlite_cursor.execute("SELECT id, wechat_openid, student_id, name, bind_time FROM user")
    users = sqlite_cursor.fetchall()
    
    # 连接PostgreSQL数据库
    pg_conn = psycopg2.connect(
        dbname=PG_DB,
        user=PG_USER,
        password=PG_PASSWORD,
        host=PG_HOST,
        port=PG_PORT
    )
    pg_cursor = pg_conn.cursor()
    
    # 迁移用户数据
    print(f"开始迁移用户数据，共{len(users)}条记录...")
    imported_count = 0
    
    for user in users:
        try:
            # 如果bind_time为NULL，则设置为NULL
            bind_time = user['bind_time'] if user['bind_time'] else None
            
            # 插入用户数据
            pg_cursor.execute("""
                INSERT INTO users (id, wechat_openid, student_id, name, bind_time, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO NOTHING
            """, (
                user['id'], 
                user['wechat_openid'], 
                user['student_id'], 
                user['name'], 
                bind_time,
                datetime.datetime.now(),
                datetime.datetime.now()
            ))
            
            imported_count += 1
            print(f"迁移用户: {user['name']}(学号: {user['student_id']}) 成功")
            
        except Exception as e:
            print(f"迁移用户 {user['name']}(学号: {user['student_id']}) 失败: {str(e)}")
    
    pg_conn.commit()
    print(f"用户数据迁移完成! 成功迁移: {imported_count}")
    
    # 关闭连接
    sqlite_conn.close()
    pg_conn.close()

def migrate_song_requests():
    """迁移歌曲请求数据"""
    # 连接SQLite数据库
    sqlite_conn = sqlite3.connect(SQLITE_DB)
    sqlite_conn.row_factory = sqlite3.Row
    sqlite_cursor = sqlite_conn.cursor()
    
    # 获取所有歌曲请求
    sqlite_cursor.execute("""
        SELECT id, user_id, song_id, status, request_time, review_time, review_reason, reviewer_id
        FROM song_request
    """)
    song_requests = sqlite_cursor.fetchall()
    
    # 连接PostgreSQL数据库
    pg_conn = psycopg2.connect(
        dbname=PG_DB,
        user=PG_USER,
        password=PG_PASSWORD,
        host=PG_HOST,
        port=PG_PORT
    )
    pg_cursor = pg_conn.cursor()
    
    # 迁移歌曲请求数据
    print(f"开始迁移歌曲请求数据，共{len(song_requests)}条记录...")
    imported_count = 0
    
    for req in song_requests:
        try:
            # 如果review_time为NULL，则设置为NULL
            review_time = req['review_time'] if req['review_time'] else None
            
            # 插入歌曲请求数据
            pg_cursor.execute("""
                INSERT INTO song_requests (
                    id, user_id, song_id, status, request_time, review_time, review_reason, reviewer_id,
                    created_at, updated_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO NOTHING
            """, (
                req['id'], 
                req['user_id'], 
                req['song_id'], 
                req['status'],
                req['request_time'],
                review_time,
                req['review_reason'],
                req['reviewer_id'],
                datetime.datetime.now(),
                datetime.datetime.now()
            ))
            
            imported_count += 1
            print(f"迁移歌曲请求ID: {req['id']} 成功")
            
        except Exception as e:
            print(f"迁移歌曲请求ID: {req['id']} 失败: {str(e)}")
    
    pg_conn.commit()
    print(f"歌曲请求数据迁移完成! 成功迁移: {imported_count}")
    
    # 关闭连接
    sqlite_conn.close()
    pg_conn.close()

def migrate_refresh_tokens():
    """迁移刷新令牌数据"""
    # 连接SQLite数据库
    sqlite_conn = sqlite3.connect(SQLITE_DB)
    sqlite_conn.row_factory = sqlite3.Row
    sqlite_cursor = sqlite_conn.cursor()
    
    # 检查refresh_tokens表是否存在
    sqlite_cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='refresh_tokens'")
    if not sqlite_cursor.fetchone():
        print("SQLite中没有refresh_tokens表，跳过迁移")
        sqlite_conn.close()
        return
    
    # 获取所有刷新令牌
    sqlite_cursor.execute("""
        SELECT id, openid, token_id, expires_at, created_at
        FROM refresh_tokens
    """)
    refresh_tokens = sqlite_cursor.fetchall()
    
    # 连接PostgreSQL数据库
    pg_conn = psycopg2.connect(
        dbname=PG_DB,
        user=PG_USER,
        password=PG_PASSWORD,
        host=PG_HOST,
        port=PG_PORT
    )
    pg_cursor = pg_conn.cursor()
    
    # 迁移刷新令牌数据
    print(f"开始迁移刷新令牌数据，共{len(refresh_tokens)}条记录...")
    imported_count = 0
    
    for token in refresh_tokens:
        try:
            # 插入刷新令牌数据
            pg_cursor.execute("""
                INSERT INTO refresh_tokens (
                    id, openid, token_id, expires_at, created_at, updated_at
                )
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (openid, token_id) DO NOTHING
            """, (
                token['id'], 
                token['openid'], 
                token['token_id'], 
                token['expires_at'],
                token['created_at'],
                datetime.datetime.now()
            ))
            
            imported_count += 1
            print(f"迁移刷新令牌ID: {token['id']} 成功")
            
        except Exception as e:
            print(f"迁移刷新令牌ID: {token['id']} 失败: {str(e)}")
    
    pg_conn.commit()
    print(f"刷新令牌数据迁移完成! 成功迁移: {imported_count}")
    
    # 关闭连接
    sqlite_conn.close()
    pg_conn.close()

if __name__ == "__main__":
    argparser = argparse.ArgumentParser(description="数据库迁移脚本")
    argparser.add_argument('--delete', action='store_true', help='删除现有的PostgreSQL表并重新创建')
    args = argparser.parse_args()
    if args.delete:
        print("删除现有的PostgreSQL表...")

    # 创建PostgreSQL数据库表
    create_postgres_tables(args.delete)
    
    # 迁移数据
    migrate_users()
    migrate_song_requests()
    migrate_refresh_tokens()
    
    print("数据库初始化完成!")