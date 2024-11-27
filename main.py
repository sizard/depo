import logging
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, 
    ConversationHandler, 
    CommandHandler,
    ContextTypes
)
import os
from dotenv import load_dotenv
from models import Base, User
from database import engine, Session
from handlers.registration import registration_handler, start_registration
from handlers.common import show_main_menu, cancel
from handlers.admin import admin_handler
from handlers.profile import profile_handler, edit_profile_handler
from handlers.reception import reception_handler

# Загружаем переменные окружения
load_dotenv()

# Настраиваем логирование
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

TOKEN = os.getenv('BOT_TOKEN')

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    # Проверяем, зарегистрирован ли пользователь
    with Session() as session:
        user = session.query(User).filter(User.id == update.effective_user.id).first()
        if user:
            return await show_main_menu(update, context)
        else:
            await update.message.reply_text(
                '👋 Добро пожаловать! Для начала работы необходимо зарегистрироваться.\n'
                'Используйте команду /register'
            )

def main():
    """Основная функция запуска бота"""
    # Создаем таблицы в базе данных
    Base.metadata.create_all(engine)
    
    # Инициализируем бота
    application = ApplicationBuilder().token(TOKEN).build()
    
    # Добавляем обработчики в правильном порядке
    application.add_handler(CommandHandler("start", start))  # Сначала /start
    application.add_handler(registration_handler)  # Обработчик регистрации
    application.add_handler(admin_handler)  # Админский обработчик
    application.add_handler(edit_profile_handler)  # Обработчик редактирования профиля
    application.add_handler(profile_handler)  # Обработчик просмотра профиля
    application.add_handler(reception_handler)  # Обработчик приёмки составов
    application.add_handler(CommandHandler("cancel", cancel))  # Обработчик отмены
    
    # Запускаем бота
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
