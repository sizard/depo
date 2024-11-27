from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ContextTypes, ConversationHandler
from models import User
from database import session_scope

async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает главное меню"""
    # Проверяем, является ли пользователь администратором
    is_admin = False
    with session_scope() as session:
        user = session.query(User).filter(User.id == update.effective_user.id).first()
        if user and user.is_admin:
            is_admin = True
    
    # Базовые кнопки для всех пользователей
    keyboard = [
        [KeyboardButton('🚂 Приёмка состава')],
        [KeyboardButton('👤 Мой профиль')]
    ]
    
    # Добавляем кнопку админ-панели для администраторов
    if is_admin:
        keyboard.append([KeyboardButton('⚙️ Панель администратора')])
    
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text(
        '🎯 <b>Главное меню</b>\n'
        'Выберите действие:',
        reply_markup=reply_markup,
        parse_mode='HTML'
    )
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отменяет текущее действие и возвращает в главное меню"""
    await update.message.reply_text(
        '❌ Действие отменено.\n'
        '↩️ Возвращаемся в главное меню...'
    )
    return await show_main_menu(update, context)
