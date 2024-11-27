from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    MessageHandler,
    filters
)
from models import User, UserRole, Railway
from database import session_scope
from .common import show_main_menu, cancel
from .notifications import notify_admins

# Состояния регистрации
ENTER_FULLNAME, ENTER_POSITION, ENTER_RAILWAY, ENTER_BRANCH, ENTER_PHONE = range(5)

async def start_registration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало регистрации"""
    # Проверяем, зарегистрирован ли пользователь
    with session_scope() as session:
        user = session.query(User).filter(User.id == update.effective_user.id).first()
        if user:
            await update.message.reply_text(
                f'👋 С возвращением, {user.full_name}!'
            )
            return await show_main_menu(update, context)

    # Если пользователь не зарегистрирован, начинаем регистрацию
    await update.message.reply_text(
        '👋 Добро пожаловать в систему управления депо!\n\n'
        '📝 Давайте начнем регистрацию.\n'
        '👤 Введите ваше ФИО:'
    )
    return ENTER_FULLNAME

async def process_fullname(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка ФИО"""
    full_name = update.message.text.strip()
    if len(full_name.split()) < 2:
        await update.message.reply_text(
            '⚠️ Пожалуйста, введите полное ФИО\n'
            'Например: Иванов Иван Иванович'
        )
        return ENTER_FULLNAME
    
    context.user_data['full_name'] = full_name
    
    await update.message.reply_text(
        '✅ Отлично! Теперь введите вашу должность:\n'
        'Например: Машинист, Помощник машиниста, Дежурный по депо'
    )
    return ENTER_POSITION

async def process_position(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка должности"""
    position = update.message.text.strip()
    if len(position) < 3:
        await update.message.reply_text(
            '⚠️ Пожалуйста, введите корректную должность'
        )
        return ENTER_POSITION
    
    context.user_data['position'] = position
    
    # Создаем клавиатуру с дорогами
    keyboard = [[KeyboardButton(railway.value)] for railway in Railway]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text(
        '🚂 Выберите вашу дорогу:',
        reply_markup=reply_markup
    )
    return ENTER_RAILWAY

async def process_railway(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка выбора дороги"""
    railway = update.message.text.strip()
    
    # Проверяем, что выбрана существующая дорога
    try:
        selected_railway = next(r for r in Railway if r.value == railway)
        context.user_data['railway'] = selected_railway
    except StopIteration:
        await update.message.reply_text('⚠️ Пожалуйста, выберите дорогу из списка')
        return ENTER_RAILWAY
    
    await update.message.reply_text(
        '🏢 Введите ваше отделение:',
        reply_markup=ReplyKeyboardRemove()
    )
    return ENTER_BRANCH

async def process_branch(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка отделения"""
    branch = update.message.text.strip()
    if len(branch) < 2:
        await update.message.reply_text('⚠️ Пожалуйста, введите корректное отделение')
        return ENTER_BRANCH
    
    context.user_data['branch'] = branch
    
    await update.message.reply_text(
        '📱 Введите ваш номер телефона:\n'
        'Например: +79001234567'
    )
    return ENTER_PHONE

async def process_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка номера телефона и завершение регистрации"""
    phone = update.message.text.strip()
    if not phone.startswith('+') or not phone[1:].isdigit() or len(phone) < 10:
        await update.message.reply_text(
            '⚠️ Пожалуйста, введите корректный номер телефона\n'
            'Например: +79001234567'
        )
        return ENTER_PHONE
    
    # Сохраняем данные пользователя
    try:
        with session_scope() as session:
            user = User(
                id=update.effective_user.id,
                username=update.effective_user.username,
                full_name=context.user_data['full_name'],
                position=context.user_data['position'],
                railway=context.user_data['railway'],
                branch=context.user_data['branch'],
                phone=phone,
                role=UserRole.USER,
                is_active=True
            )
            session.add(user)
            session.flush()  # Убеждаемся, что у объекта есть все данные
            
            # Сохраняем данные пользователя для использования после закрытия сессии
            user_data = {
                'full_name': user.full_name,
                'position': user.position,
                'railway': user.railway.value,
                'branch': user.branch,
                'phone': user.phone
            }
            
        # Уведомляем администраторов о новой регистрации
        await notify_admins(
            context,
            f'📝 Новая регистрация!\n\n'
            f'👤 {user_data["full_name"]}\n'
            f'📋 Должность: {user_data["position"]}\n'
            f'🚂 Дорога: {user_data["railway"]}\n'
            f'🏢 Отделение: {user_data["branch"]}\n'
            f'📱 Телефон: {user_data["phone"]}'
        )
        
        # Отправляем приветственное сообщение
        await update.message.reply_text(
            f'✅ Регистрация успешно завершена!\n\n'
            f'👤 {user_data["full_name"]}\n'
            f'📋 Должность: {user_data["position"]}\n'
            f'🚂 Дорога: {user_data["railway"]}\n'
            f'🏢 Отделение: {user_data["branch"]}\n'
            f'📱 Телефон: {user_data["phone"]}\n\n'
            f'Добро пожаловать в систему! 🎉'
        )
        
        # Показываем главное меню
        return await show_main_menu(update, context)
            
    except Exception as e:
        print(f"❌ Ошибка при регистрации: {str(e)}")
        await update.message.reply_text(
            '❌ Произошла ошибка при регистрации.\n'
            'Пожалуйста, попробуйте еще раз позже или обратитесь к администратору.'
        )
        return ConversationHandler.END

# Создаем обработчик регистрации
registration_handler = ConversationHandler(
    entry_points=[CommandHandler("register", start_registration)],
    states={
        ENTER_FULLNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_fullname)],
        ENTER_POSITION: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_position)],
        ENTER_RAILWAY: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_railway)],
        ENTER_BRANCH: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_branch)],
        ENTER_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_phone)],
    },
    fallbacks=[CommandHandler('cancel', cancel)]
)
