from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler, MessageHandler, filters
from models import User, UserRole
from database import session_scope
from .common import show_main_menu

# Состояния админского меню
ADMIN_MENU, VIEW_USERS, MANAGE_USER = range(3)

async def admin_required(func):
    """Декоратор для проверки прав администратора"""
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        with session_scope() as session:
            user = session.query(User).filter(User.id == update.effective_user.id).first()
            if not user or not user.is_admin:
                await update.message.reply_text(
                    '⛔️ У вас нет прав администратора для выполнения этой команды.'
                )
                return ConversationHandler.END
        return await func(update, context)
    return wrapper

@admin_required
async def admin_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать админское меню"""
    keyboard = [
        [KeyboardButton("👥 Просмотр пользователей")],
        [KeyboardButton("👑 Назначить администратора")],
        [KeyboardButton("❌ Заблокировать пользователя")],
        [KeyboardButton("🔙 Вернуться в главное меню")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text(
        '🛠 Панель администратора\n'
        'Выберите действие:',
        reply_markup=reply_markup
    )
    return ADMIN_MENU

@admin_required
async def view_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Просмотр списка пользователей"""
    with session_scope() as session:
        users = session.query(User).all()
        
        if not users:
            await update.message.reply_text('📝 Список пользователей пуст.')
            return ADMIN_MENU
        
        message = "📋 Список пользователей:\n\n"
        for user in users:
            message += (
                f"👤 {user.last_name} {user.first_name}\n"
                f"💼 Должность: {user.position}\n"
                f"🚂 Дорога: {user.railway.value}\n"
                f"🏢 Отделение: {user.branch}\n"
                f"🎭 Роль: {user.role.value}\n"
                f"🆔 ID: {user.id}\n"
                "➖➖➖➖➖➖➖➖➖➖\n"
            )
        
        await update.message.reply_text(message)
    return ADMIN_MENU

@admin_required
async def set_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Назначение пользователя администратором"""
    try:
        user_id = int(context.args[0])
    except (ValueError, IndexError):
        await update.message.reply_text(
            '⚠️ Пожалуйста, укажите корректный ID пользователя.\n'
            'Пример: /set_admin 123456789'
        )
        return ADMIN_MENU
    
    with session_scope() as session:
        user = session.query(User).filter(User.id == user_id).first()
        if not user:
            await update.message.reply_text('❌ Пользователь не найден.')
            return ADMIN_MENU
        
        user.role = UserRole.ADMIN
        
        await update.message.reply_text(
            f'✅ Пользователь {user.last_name} {user.first_name} '
            f'назначен администратором.'
        )
    return ADMIN_MENU

@admin_required
async def block_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Блокировка пользователя"""
    # В будущем можно добавить функционал блокировки
    await update.message.reply_text(
        '🚧 Функция блокировки пользователей находится в разработке.'
    )
    return ADMIN_MENU

async def handle_admin_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка выбора в админском меню"""
    choice = update.message.text
    
    if choice == "👥 Просмотр пользователей":
        return await view_users(update, context)
    elif choice == "👑 Назначить администратора":
        await update.message.reply_text(
            '📝 Используйте команду /set_admin с ID пользователя.\n'
            'Пример: /set_admin 123456789'
        )
        return ADMIN_MENU
    elif choice == "❌ Заблокировать пользователя":
        return await block_user(update, context)
    elif choice == "🔙 Вернуться в главное меню":
        return await show_main_menu(update, context)
    
    await update.message.reply_text('❓ Пожалуйста, выберите действие из меню.')
    return ADMIN_MENU

# Создаем обработчик админского меню
admin_handler = ConversationHandler(
    entry_points=[CommandHandler("admin", admin_menu)],
    states={
        ADMIN_MENU: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_admin_menu),
            CommandHandler("set_admin", set_admin)
        ]
    },
    fallbacks=[CommandHandler("cancel", show_main_menu)]
)
