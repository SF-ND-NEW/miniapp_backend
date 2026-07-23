import psycopg2
from sqlalchemy import create_engine
from sqlalchemy.exc import ProgrammingError

from app.core.config import settings
from app.db.session import Base, engine
from app.db.models import User, SongRequest, RefreshToken, WallMessage, GradeFile


def create_database_if_not_exists() -> None:
    """
    检查数据库是否存在，如果不存在则创建
    """
    # 构建连接到默认 'postgres' 数据库的连接信息
    conn_params = {
        'dbname': 'postgres',
        'user': settings.POSTGRES_USER,
        'password': settings.POSTGRES_PASSWORD,
        'host': settings.POSTGRES_HOST,
        'port': settings.POSTGRES_PORT,
    }
    
    try:
        # 先尝试连接到目标数据库
        test_engine = create_engine(settings.DATABASE_URI)
        with test_engine.connect():
            print(f"数据库 '{settings.POSTGRES_DB}' 已存在")
            return
    except ProgrammingError as e:
        # 如果数据库不存在，尝试创建
        if "database " in str(e).lower():
            pass
        else:
            raise
    except Exception:
        # 其他连接错误，继续尝试创建
        pass
    
    try:
        # 连接到默认的 postgres 数据库来创建新数据库
        conn = psycopg2.connect(**conn_params)
        conn.autocommit = True
        cursor = conn.cursor()
        
        cursor.execute(f"SELECT 1 FROM pg_database WHERE datname = '{settings.POSTGRES_DB}'")
        exists = cursor.fetchone()
        
        if not exists:
            cursor.execute(f"CREATE DATABASE {settings.POSTGRES_DB}")
            print(f"数据库 '{settings.POSTGRES_DB}' 创建成功")
        else:
            print(f"数据库 '{settings.POSTGRES_DB}' 已存在")
        
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"创建数据库失败: {str(e)}")
        raise


def create_tables_if_not_exists() -> None:
    """
    创建所有数据库表（如果不存在）
    """
    try:
        # 确保数据库存在
        create_database_if_not_exists()
        
        # 创建所有表
        Base.metadata.create_all(bind=engine)
        print("数据库表创建完成")
    except Exception as e:
        print(f"创建数据库表失败: {str(e)}")
        raise


def init_database() -> None:
    """
    初始化数据库：创建数据库（如果不存在）和所有表（如果不存在）
    """
    print("开始初始化数据库...")
    create_tables_if_not_exists()
    print("数据库初始化完成")


if __name__ == "__main__":
    init_database()