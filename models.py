from enum import Enum
from datetime import datetime
from sqlalchemy import (
    Column, 
    Integer, 
    String, 
    DateTime, 
    ForeignKey,
    Enum as SQLEnum,
    Boolean
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from database import engine

# Создаем базовый класс для моделей
Base = declarative_base()

class Railway(str, Enum):
    """Типы железных дорог"""
    YUGO_VOSTOCHNAYA = "Юго-Восточная ЖД"
    MOSKOVSKAYA = "Московская ЖД"
    PRIVOLZHSKAYA = "Приволжская ЖД"
    SEVERO_KAVKAZSKAYA = "Северо-Кавказская ЖД"
    KALININGRADSKAYA = "Калининградская ЖД"
    GORKOVSKAYA = "Горьковская ЖД"
    DALNEVOSTOCHNAYA = "Дальневосточная ЖД"
    ZABAIKALSKAYA = "Забайкальская ЖД"
    ZAPADNOSIBIRSKAYA = "Западно-Сибирская ЖД"
    KRASNOYARSKAYA = "Красноярская ЖД"
    KUYBYSHEVSKAYA = "Куйбышевская ЖД"
    OKTYABRSKAYA = "Октябрьская ЖД"
    SVERDLOVSKAYA = "Свердловская ЖД"
    SEVERO_ZAPADNAYA = "Северо-Западная ЖД"
    SEVERNAYA = "Северная ЖД"
    YUGO_ZAPADNAYA = "Юго-Западная ЖД"

class TrainType(str, Enum):
    """Типы составов"""
    ELEKTRICHKA = "Электричка"
    RAIL_BUS = "Рельсовый автобус"

class UserRole(str, Enum):
    """Роли пользователей"""
    USER = "USER"
    ADMIN = "ADMIN"

class User(Base):
    """Модель пользователя"""
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    username = Column(String, nullable=True)
    full_name = Column(String, nullable=False)
    position = Column(String, nullable=False)
    railway = Column(SQLEnum(Railway), nullable=False)
    branch = Column(String, nullable=False)
    phone = Column(String, nullable=False)
    role = Column(SQLEnum(UserRole), default=UserRole.USER)
    is_active = Column(Boolean, default=True)
    
    # Отношения
    receptions = relationship("TrainReception", back_populates="user")
    
    @property
    def is_admin(self):
        return self.role == UserRole.ADMIN

class TrainReception(Base):
    """Модель приёмки состава"""
    __tablename__ = 'train_receptions'

    id = Column(Integer, primary_key=True)
    train_number = Column(String, nullable=False)
    train_type = Column(SQLEnum(TrainType), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    created_at = Column(DateTime, default=datetime.now)
    is_completed = Column(Boolean, default=False)
    
    # Отношения
    user = relationship("User", back_populates="receptions")
    blocks = relationship("BlockInTrain", back_populates="reception")

class BlockInTrain(Base):
    """Модель блока в составе"""
    __tablename__ = 'blocks_in_train'

    id = Column(Integer, primary_key=True)
    reception_id = Column(Integer, ForeignKey('train_receptions.id'), nullable=False)
    block_number = Column(String, nullable=False)
    is_checked = Column(Boolean, default=False)
    notes = Column(String, nullable=True)  # Добавляем поле для заметок
    
    # Отношения
    reception = relationship("TrainReception", back_populates="blocks")

# Создаем все таблицы
Base.metadata.create_all(engine)
