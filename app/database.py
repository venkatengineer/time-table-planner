from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# 🔹 Change this if you switch to MySQL later
DATABASE_URL = "sqlite:///./timetable.db"

# Create engine
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}  # needed for SQLite
)

# Create session (to talk to DB)
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Base class for models
Base = declarative_base()


# 🔹 Dependency (use later in routes)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()