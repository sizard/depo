import logging
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, 
    ConversationHandler, 
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    CallbackQueryHandler
)
import os
from dotenv import load_dotenv
from models import Base, User
from database import engine, Session
from handlers.registration import registration_handler, start_registration
from handlers.common import show_main_menu, cancel
from handlers.admin import admin_handler
from handlers.profile import profile_handler, edit_profile_handler
from handlers.reception import (
    reception_handler, 
    show_reception_history,
    handle_history_selection,
    VIEW_HISTORY as RECEPTION_VIEW_HISTORY
)

# Загружаем переменные окружения
load_dotenv()

# Настраиваем логирование
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

TOKEN = os.getenv('BOT_TOKEN')

VIEW_HISTORY = 1

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

async def check_user_access(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Проверяет доступ пользователя к боту"""
    with Session() as session:
        user = session.query(User).filter(User.id == update.effective_user.id).first()
        
        if not user:
            await update.message.reply_text(
                "🚫 У вас нет доступа к боту.\n"
                "Для получения доступа обратитесь к администратору."
            )
            return False
        
        if user.is_blocked:
            await update.message.reply_text(
                "⛔️ Ваш аккаунт заблокирован.\n"
                "Для разблокировки обратитесь к администратору."
            )
            return False
        
        return True

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик всех текстовых сообщений"""
    if not await check_user_access(update, context):
        return ConversationHandler.END

def main():
    """Основная функция запуска бота"""
    # Инициализируем бота
    application = ApplicationBuilder().token(TOKEN).build()
    
    # Добавляем обработчики в правильном порядке
    application.add_handler(CommandHandler("start", start))  # Сначала /start
    application.add_handler(registration_handler)  # Обработчик регистрации
    application.add_handler(admin_handler)  # Админский обработчик
    application.add_handler(edit_profile_handler)  # Обработчик редактирования профиля
    application.add_handler(profile_handler)  # Обработчик просмотра профиля
    
    # Добавляем обработчик приёмки составов
    application.add_handler(reception_handler)  # Обработчик приёмки составов
    
    # Добавляем глобальный обработчик для истории приёмок из главного меню
    application.add_handler(MessageHandler(
        filters.Text(['📋 История приёмок']) & ~filters.COMMAND,
        show_reception_history
    ))
    
    # Добавляем глобальный обработчик для callback_query
    application.add_handler(CallbackQueryHandler(
        handle_history_selection,
        pattern=r'^(view_reception_\d+|back_to_reception|export_pdf_\d+)$'
    ))
    
    # Добавляем обработчик отмены
    application.add_handler(CommandHandler("cancel", cancel))
    
    # Запускаем бота
    print("Бот запущен!")
    application.run_polling()

if __name__ == '__main__':
    main()
