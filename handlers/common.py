from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ContextTypes, ConversationHandler
from models import User
from database import session_scope

async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает главное меню"""
    with session_scope() as session:
        user = session.query(User).filter(User.id == update.effective_user.id).first()
        
        keyboard = [
            [KeyboardButton("🚂 Приёмка состава")],
            [KeyboardButton("📋 История приёмок")],
            [KeyboardButton("👤 Мой профиль")]
        ]
        
        # Добавляем кнопку админки для администраторов
        if user and user.is_admin:
            keyboard.append([KeyboardButton("⚙️ Панель администратора")])
        
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        
        await update.message.reply_text(
            f'👋 Добро пожаловать, {user.full_name if user else "гость"}!\n'
            'Выберите действие:',
            reply_markup=reply_markup
        )
    
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отмена текущего действия и возврат в главное меню"""
    await show_main_menu(update, context)
    return ConversationHandler.END
