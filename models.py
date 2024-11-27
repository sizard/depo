from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import enum

Base = declarative_base()
engine = create_engine('sqlite:///bot_database.db')
Session = sessionmaker(bind=engine)

class Railway(enum.Enum):
    GORKOVSKY = "Горьковская ж/д"
    MOSCOVSKY = "Московская ж/д"
    OKTYABRSKY = "Октябрьская ж/д"
    SEVERNY = "Северная ж/д"
    KUYBYSHEVSKY = "Куйбышевская ж/д"
    SVERDLOVSKY = "Свердловская ж/д"
    YUZHNY = "Южная ж/д"
    PRIVOLZHSKY = "Приволжская ж/д"
    ZAPADNOSIBIRSKY = "Западно-Сибирская ж/д"
    VOSTOCHNOSIBIRSKY = "Восточно-Сибирская ж/д"
    ZABAYKALSKY = "Забайкальская ж/д"
    DALNEVOSTOCHNY = "Дальневосточная ж/д"
    KALININGRADSKY = "Калининградская ж/д"
    KRASNOYARSKY = "Красноярская ж/д"
    SEVEROKAKAZSKY = "Северо-Кавказская ж/д"
    YUGOVOSTOCHNY = "Юго-Восточная ж/д"

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True)
    username = Column(String)
    first_name = Column(String)
    last_name = Column(String)
    position = Column(String)  # Должность
    railway = Column(Enum(Railway))  # Дорога
    branch = Column(String)  # Филиал
    registration_date = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)

# Создаем таблицы
Base.metadata.create_all(engine)
