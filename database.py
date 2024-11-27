from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from contextlib import contextmanager

# Создаем движок базы данных
engine = create_engine('sqlite:///bot.db')

# Создаем фабрику сессий
Session = scoped_session(sessionmaker(bind=engine))

@contextmanager
def session_scope():
    """Контекстный менеджер для работы с сессией базы данных"""
    session = Session()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()
        Session.remove()  # Очищаем сессию из реестра потоков
