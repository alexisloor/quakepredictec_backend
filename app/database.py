import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Leemos la variable de entorno DATABASE_URL
url_entorno = os.getenv("DATABASE_URL")

print("----------------------DEBUG----------------------------")
if url_entorno:
    print(f"VARIABLE ENCONTRADA: {url_entorno[:15]}...") 
    print("BASE DE DATOS: PostgreSQL")
else:
    print("VARIABLE 'DATABASE_URL' NO DETECTADA O VACÍA")
    print("BASE DE DATOS: SQLite")
print("--------------------------------------------------")

SQLALCHEMY_DATABASE_URL = url_entorno if url_entorno else "sqlite:///./quakepredict.db"

if SQLALCHEMY_DATABASE_URL and SQLALCHEMY_DATABASE_URL.startswith("postgres://"):
    SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace("postgres://", "postgresql://", 1)

if "sqlite" in SQLALCHEMY_DATABASE_URL:
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
    )
else:
    engine = create_engine(SQLALCHEMY_DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()