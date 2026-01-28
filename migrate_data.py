import sqlite3
import os
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

# ============================================
# НАЛАШТУВАННЯ
# ============================================

SQLITE_PATH = "newflask.db"  # Твій скачаний файл

# 🔴 ВСТАВЛЯЙ СЮДИ EXTERNAL DATABASE URL (БЕЗ -a!)
POSTGRES_URL = "postgresql://books_db_cjcp_user:by5by47ekvjOeubp8cOdoUHAezJMQ040@dpg-d5t3nacoud1c7395eul0.oregon-postgres.render.com/books_db_cjcp"

# ============================================
# МОДЕЛІ
# ============================================

Base = declarative_base()

class Book(Base):
    __tablename__ = 'book'
    id = Column(Integer, primary_key=True)
    name_book = Column(String(100), nullable=False)
    author = Column(String(100), nullable=False)
    surname = Column(String(100), default='')
    ean = Column(Text, nullable=False)
    buyer = Column(String(100), nullable=False)
    phone = Column(String(20), nullable=False)
    stat = Column(String(20), nullable=False)
    date = Column(DateTime, default=datetime.utcnow)
    enddate = Column(DateTime, default=datetime.utcnow)
    history = Column(Text, default='')

class Reader(Base):
    __tablename__ = 'reader'
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    surname = Column(String(100), nullable=False)
    phone = Column(String(20), nullable=False)

class User(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    username = Column(String(80), unique=True, nullable=False)
    password_hash = Column(String(200), nullable=False)
    role = Column(String(20), default='admin')

# ============================================
# МІГРАЦІЯ
# ============================================

def migrate():
    print("🚀 Починаємо міграцію...")
    
    if not os.path.exists(SQLITE_PATH):
        print(f"❌ Файл {SQLITE_PATH} не знайдено!")
        return
    
    # Підключення до SQLite
    sqlite_conn = sqlite3.connect(SQLITE_PATH)
    sqlite_cursor = sqlite_conn.cursor()
    
    # Підключення до Postgres
    engine = create_engine(
    POSTGRES_URL,
    connect_args={
        "sslmode": "require",
        "connect_timeout": 10
    }
)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # ===== BOOKS =====
        print("📚 Міграція книг...")
        try:
            sqlite_cursor.execute("SELECT * FROM book")
            books = sqlite_cursor.fetchall()
            
            for b in books:
                book = Book(
                    id=b[0],
                    name_book=b[1],
                    author=b[2],
                    surname=b[3] if len(b) > 3 else '',
                    ean=b[4] if len(b) > 4 else '',
                    buyer=b[5] if len(b) > 5 else '',
                    phone=b[6] if len(b) > 6 else '',
                    stat=b[7] if len(b) > 7 else 'доступна',
                    date=b[8] if len(b) > 8 else None,
                    enddate=b[9] if len(b) > 9 else None,
                    history=b[10] if len(b) > 10 else ''
                )
                session.merge(book)
            
            print(f"✅ Перенесено {len(books)} книг")
        except Exception as e:
            print(f"⚠️ Помилка книг: {e}")
        
        # ===== READERS =====
        print("👥 Міграція читачів...")
        try:
            sqlite_cursor.execute("SELECT * FROM reader")
            readers = sqlite_cursor.fetchall()
            
            for r in readers:
                reader = Reader(
                    id=r[0],
                    name=r[1],
                    surname=r[2],
                    phone=r[3]
                )
                session.merge(reader)
            
            print(f"✅ Перенесено {len(readers)} читачів")
        except Exception as e:
            print(f"⚠️ Помилка читачів: {e}")
        
        # ===== USERS =====
        print("🔐 Міграція користувачів...")
        try:
            sqlite_cursor.execute("SELECT * FROM user")
            users = sqlite_cursor.fetchall()
            
            for u in users:
                user = User(
                    id=u[0],
                    username=u[1],
                    password_hash=u[2],
                    role=u[3] if len(u) > 3 else 'admin'
                )
                session.merge(user)
            
            print(f"✅ Перенесено {len(users)} користувачів")
        except Exception as e:
            print(f"⚠️ Помилка користувачів: {e}")
        
        # Commit всіх змін
        session.commit()
        print("\n🎉 МІГРАЦІЯ ЗАВЕРШЕНА УСПІШНО!")
        
    except Exception as e:
        session.rollback()
        print(f"\n❌ ПОМИЛКА: {e}")
        import traceback
        traceback.print_exc()
    finally:
        sqlite_conn.close()
        session.close()

if __name__ == "__main__":
    migrate()