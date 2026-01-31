# app/models.py
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UniqueConstraint, Float
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=True)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # relación a suscripciones
    subscriptions = relationship("Subscription", back_populates="user", cascade="all, delete-orphan")


class City(Base):
    __tablename__ = "cities"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    province = Column(String, nullable=True)
    lat = Column(Float, nullable=False, default=0.0)
    lon = Column(Float, nullable=False, default=0.0)
    subscriptions = relationship("Subscription", back_populates="city", cascade="all, delete-orphan")


class Subscription(Base):
    __tablename__ = "subscriptions"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    city_id = Column(Integer, ForeignKey("cities.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="subscriptions")
    city = relationship("City", back_populates="subscriptions")

    # evita que el mismo usuario se suscriba 2 veces a la misma ciudad
    __table_args__ = (UniqueConstraint("user_id", "city_id", name="uq_user_city"),)

class PredictionReport(Base):
    __tablename__ = "prediction_reports"

    id = Column(Integer, primary_key=True, index=True)
    # Fecha de la predicción
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Nombre del Canton 
    location = Column(String, nullable=False, index=True)
    
    probability = Column(Float, nullable=False)
    
    risk_level = Column(String, nullable=False)