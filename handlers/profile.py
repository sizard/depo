from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    ContextTypes, 
    CommandHandler, 
    MessageHandler, 
    filters,
    ConversationHandler
)

from models import User, Railway
from database import session_scope
from handlers.common import show_main_menu, cancel

# Состояния редактирования профиля
EDIT_NAME, EDIT_POSITION, EDIT_RAILWAY, EDIT_BRANCH = range(4)

async def show_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает профиль пользователя"""
    with session_scope() as session:
        user = session.query(User).filter(User.id == update.effective_user.id).first()
        if not user:
            await update.message.reply_text(
                '❌ Ошибка: профиль не найден.\n'
                'Пожалуйста, зарегистрируйтесь с помощью команды /start'
            )
            return
        
        await update.message.reply_text(
            '👤 <b>Ваш профиль</b>\n\n'
            f'📋 ФИО: {user.full_name}\n'
            f'💼 Должность: {user.position}\n'
            f'🚂 Дорога: {user.railway.value}\n'
            f'🏢 Отделение: {user.branch}\n'
            f'🔑 Роль: {"👑 Администратор" if user.is_admin else "👤 Пользователь"}\n\n'
            '📝 Для изменения данных используйте команду /edit_profile',
            parse_mode='HTML'
        )

async def start_edit_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало редактирования профиля"""
    await update.message.reply_text(
        '📝 <b>Редактирование профиля</b>\n\n'
        '👤 Введите ваши ФИО (Фамилия Имя Отчество):',
        parse_mode='HTML'
    )
    return EDIT_NAME

async def edit_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка ввода имени"""
    full_name = update.message.text.strip()
    if len(full_name.split()) < 2:
        await update.message.reply_text(
            '⚠️ Пожалуйста, введите полное ФИО\n'
            'Например: Иванов Иван Иванович'
        )
        return EDIT_NAME
    
    context.user_data['full_name'] = full_name
    
    await update.message.reply_text(
        '✅ ФИО обновлено!\n\n'
        '💼 Теперь введите вашу должность:'
    )
    return EDIT_POSITION

async def edit_position(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка ввода должности"""
    position = update.message.text.strip()
    if len(position) < 3:
        await update.message.reply_text(
            '⚠️ Должность должна содержать хотя бы 3 символа.\n'
            '🔄 Попробуйте еще раз:'
        )
        return EDIT_POSITION
    
    context.user_data['position'] = position
    
    # Создаем клавиатуру с дорогами
    keyboard = [[KeyboardButton(railway.value)] for railway in Railway]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text(
        '🚂 Выберите вашу дорогу:',
        reply_markup=reply_markup
    )
    return EDIT_RAILWAY

async def edit_railway(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка выбора дороги"""
    railway = update.message.text.strip()
    try:
        context.user_data['railway'] = Railway(railway)
    except ValueError:
        await update.message.reply_text(
            '⚠️ Пожалуйста, выберите дорогу из предложенных вариантов.'
        )
        return EDIT_RAILWAY
    
    await update.message.reply_text(
        '🏢 Введите ваше отделение:'
    )
    return EDIT_BRANCH

async def edit_branch(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка ввода отделения и сохранение профиля"""
    branch = update.message.text.strip()
    if len(branch) < 2:
        await update.message.reply_text('⚠️ Пожалуйста, введите корректное отделение')
        return EDIT_BRANCH
    
    try:
        with session_scope() as session:
            user = session.query(User).filter(User.id == update.effective_user.id).first()
            if not user:
                await update.message.reply_text('❌ Ошибка: пользователь не найден')
                return ConversationHandler.END
            
            # Обновляем данные пользователя
            user.full_name = context.user_data['full_name']
            user.position = context.user_data['position']
            user.railway = context.user_data['railway']
            user.branch = branch
            
            # Сохраняем изменения
            session.commit()
            
            await update.message.reply_text(
                '✅ Профиль успешно обновлен!\n\n'
                f'👤 ФИО: {user.full_name}\n'
                f'💼 Должность: {user.position}\n'
                f'🚂 Дорога: {user.railway.value}\n'
                f'🏢 Отделение: {user.branch}'
            )
            
            return await show_main_menu(update, context)
            
    except Exception as e:
        print(f"❌ Ошибка при обновлении профиля: {str(e)}")
        await update.message.reply_text(
            '❌ Произошла ошибка при обновлении профиля.\n'
            'Пожалуйста, попробуйте еще раз позже или обратитесь к администратору.'
        )
        return ConversationHandler.END

# Создаем обработчик для редактирования профиля
edit_profile_handler = ConversationHandler(
    entry_points=[CommandHandler('edit_profile', start_edit_profile)],
    states={
        EDIT_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_name)],
        EDIT_POSITION: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_position)],
        EDIT_RAILWAY: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_railway)],
        EDIT_BRANCH: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_branch)],
    },
    fallbacks=[CommandHandler('cancel', cancel)]
)

# Создаем обработчик для кнопки "Мой профиль"
profile_handler = MessageHandler(
    filters.Text(["👤 Мой профиль"]), 
    show_profile
)
