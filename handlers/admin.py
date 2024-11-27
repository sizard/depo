from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler, MessageHandler, filters, CallbackQueryHandler
from models import User, UserRole
from database import session_scope
from .common import show_main_menu

# Состояния админского меню
ADMIN_MENU, VIEW_USERS, SELECT_USER, CONFIRM_ACTION = range(4)

def admin_required(func):
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
        [KeyboardButton("👥 Управление пользователями")],
        [KeyboardButton("📊 Статистика")],
        [KeyboardButton("🔙 Вернуться в главное меню")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text(
        '⚙️ Панель администратора\n'
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
        
        # Создаем инлайн-кнопки для каждого пользователя
        keyboard = []
        for user in users:
            status = "👑" if user.is_admin else "🚫" if user.is_blocked else "✅"
            button = InlineKeyboardButton(
                f"{status} {user.full_name} ({user.position})",
                callback_data=f"user_{user.id}"
            )
            keyboard.append([button])
        
        keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="back_to_admin")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "👥 Список пользователей\n"
            "Нажмите на пользователя для управления:",
            reply_markup=reply_markup
        )
        return SELECT_USER

@admin_required
async def handle_user_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка выбора пользователя"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "back_to_admin":
        await admin_menu(update, context)
        return ADMIN_MENU
    
    user_id = int(query.data.split('_')[1])
    context.user_data['selected_user_id'] = user_id
    
    with session_scope() as session:
        user = session.query(User).get(user_id)
        if not user:
            await query.message.edit_text("❌ Пользователь не найден")
            return ADMIN_MENU
        
        status = "Администратор" if user.is_admin else "Заблокирован" if user.is_blocked else "Активен"
        
        # Создаем кнопки действий
        keyboard = []
        if not user.is_admin:
            keyboard.append([InlineKeyboardButton("👑 Назначить администратором", 
                                                callback_data=f"make_admin_{user_id}")])
        if user.is_blocked:
            keyboard.append([InlineKeyboardButton("✅ Разблокировать", 
                                                callback_data=f"unblock_{user_id}")])
        else:
            keyboard.append([InlineKeyboardButton("🚫 Заблокировать", 
                                                callback_data=f"block_{user_id}")])
        
        keyboard.append([InlineKeyboardButton("🔙 Назад к списку", callback_data="back_to_list")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.message.edit_text(
            f"👤 Пользователь: {user.full_name}\n"
            f"📱 Telegram ID: {user.id}\n"
            f"📋 Должность: {user.position}\n"
            f"🏢 Отделение: {user.branch}\n"
            f"🔑 Статус: {status}\n\n"
            "Выберите действие:",
            reply_markup=reply_markup
        )
        return CONFIRM_ACTION

@admin_required
async def handle_user_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка действий с пользователем"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "back_to_list":
        await view_users(update, context)
        return SELECT_USER
    
    action, user_id = query.data.split('_')[0:2]
    user_id = int(user_id)
    
    with session_scope() as session:
        user = session.query(User).get(user_id)
        if not user:
            await query.message.edit_text("❌ Пользователь не найден")
            return ADMIN_MENU
        
        if action == "make_admin":
            user.is_admin = True
            message = f"👑 Пользователь {user.full_name} назначен администратором"
        elif action == "block":
            user.is_blocked = True
            message = f"🚫 Пользователь {user.full_name} заблокирован"
        elif action == "unblock":
            user.is_blocked = False
            message = f"✅ Пользователь {user.full_name} разблокирован"
        
        session.commit()
        
        # Отправляем уведомление пользователю о изменении его статуса
        try:
            if action == "make_admin":
                await context.bot.send_message(
                    user_id,
                    "🎉 Поздравляем! Вам предоставлены права администратора."
                )
            elif action == "block":
                await context.bot.send_message(
                    user_id,
                    "⛔️ Ваш аккаунт был заблокирован администратором."
                )
            elif action == "unblock":
                await context.bot.send_message(
                    user_id,
                    "✅ Ваш аккаунт был разблокирован администратором."
                )
        except:
            pass  # Игнорируем ошибки отправки уведомлений
        
        await query.message.edit_text(
            f"{message}\n"
            "Возвращаемся к списку пользователей..."
        )
        await view_users(update, context)
        return SELECT_USER

@admin_required
async def show_statistics(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать статистику"""
    with session_scope() as session:
        total_users = session.query(User).count()
        admin_users = session.query(User).filter(User.is_admin == True).count()
        blocked_users = session.query(User).filter(User.is_blocked == True).count()
        active_users = total_users - blocked_users
        
        await update.message.reply_text(
            "📊 Статистика системы\n\n"
            f"👥 Всего пользователей: {total_users}\n"
            f"✅ Активных пользователей: {active_users}\n"
            f"👑 Администраторов: {admin_users}\n"
            f"🚫 Заблокированных: {blocked_users}\n"
        )
        return ADMIN_MENU

@admin_required
async def handle_admin_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка выбора в админском меню"""
    text = update.message.text
    
    if text == "👥 Управление пользователями":
        return await view_users(update, context)
    elif text == "📊 Статистика":
        return await show_statistics(update, context)
    elif text == "🔙 Вернуться в главное меню":
        return await show_main_menu(update, context)
    else:
        await update.message.reply_text("❌ Неизвестная команда")
        return ADMIN_MENU

# Создаем обработчик админского меню
admin_handler = ConversationHandler(
    entry_points=[
        MessageHandler(filters.Text(["⚙️ Панель администратора"]), admin_menu),
        CommandHandler("admin", admin_menu)
    ],
    states={
        ADMIN_MENU: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_admin_menu)
        ],
        SELECT_USER: [
            CallbackQueryHandler(handle_user_selection)
        ],
        CONFIRM_ACTION: [
            CallbackQueryHandler(handle_user_action)
        ]
    },
    fallbacks=[
        MessageHandler(filters.Text(["🔙 Вернуться в главное меню"]), show_main_menu),
        CommandHandler("cancel", show_main_menu)
    ]
)
