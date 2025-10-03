# # backend/database.py
# from sqlalchemy import create_engine
# from sqlalchemy.orm import sessionmaker, declarative_base

# SQLALCHEMY_DATABASE_URL = "sqlite:///./taskai.db"

# # For SQLite in multi-threaded apps:
# engine = create_engine(
#     SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
# )

# SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base = declarative_base()


import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Use DATABASE_URL from env, fallback to SQLite file
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./taskai.db")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

