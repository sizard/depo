import os
import logging
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler, CallbackQueryHandler
from telegram.error import TelegramError
from models import Session, User, Railway
from sqlalchemy import func

# Загрузка переменных окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Получаем ID админа из переменных окружения
ADMIN_ID = int(os.getenv('ADMIN_ID'))

# Состояния для регистрации
ENTER_FIRST_NAME, ENTER_LAST_NAME, ENTER_POSITION, CHOOSE_RAILWAY, ENTER_BRANCH = range(5)

# Состояния для рассылки
BROADCAST_CHOOSE_TARGET, BROADCAST_ENTER_MESSAGE = range(5, 7)

def is_admin(user_id: int) -> bool:
    """Проверяет, является ли пользователь администратором"""
    return user_id == ADMIN_ID

# Декоратор для проверки прав администратора
def admin_required(func):
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not is_admin(update.effective_user.id):
            await update.message.reply_text('У вас нет прав для выполнения этой команды.')
            return
        return await func(update, context)
    return wrapper

# Обработчик команды /start
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    # Проверяем, зарегистрирован ли пользователь
    with Session() as session:
        user = session.query(User).filter(User.telegram_id == user_id).first()
        
        if user:
            keyboard = []
            if is_admin(user_id):
                keyboard.append([KeyboardButton('👥 Список пользователей')])
                keyboard.append([KeyboardButton('📨 Рассылка')])
            
            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True) if keyboard else None
            
            await update.message.reply_text(
                f'С возвращением, {user.first_name}! Вы уже зарегистрированы.',
                reply_markup=reply_markup
            )
            return ConversationHandler.END
    
    # Если пользователь не зарегистрирован
    await update.message.reply_text(
        'Добро пожаловать! Давайте начнем регистрацию.\n\nВведите ваше имя:'
    )
    
    return ENTER_FIRST_NAME

# Обработчики этапов регистрации
async def process_first_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['first_name'] = update.message.text
    await update.message.reply_text('Введите вашу фамилию:')
    return ENTER_LAST_NAME

async def process_last_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['last_name'] = update.message.text
    await update.message.reply_text('Введите вашу должность:')
    return ENTER_POSITION

async def process_position(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['position'] = update.message.text
    
    # Создаем клавиатуру с списком дорог
    keyboard = [[KeyboardButton(railway.value)] for railway in Railway]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text(
        'Выберите вашу дорогу из списка:',
        reply_markup=reply_markup
    )
    return CHOOSE_RAILWAY

async def process_railway(update: Update, context: ContextTypes.DEFAULT_TYPE):
    selected_railway = update.message.text
    # Находим enum по значению
    railway_enum = next((r for r in Railway if r.value == selected_railway), None)
    
    if not railway_enum:
        await update.message.reply_text(
            'Пожалуйста, выберите дорогу из предложенного списка.'
        )
        return CHOOSE_RAILWAY
    
    context.user_data['railway'] = railway_enum
    
    await update.message.reply_text(
        'Введите название вашего филиала:',
        reply_markup=ReplyKeyboardRemove()
    )
    return ENTER_BRANCH

async def process_branch(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    context.user_data['branch'] = update.message.text
    
    # Сохраняем пользователя в базу
    with Session() as session:
        new_user = User(
            telegram_id=user.id,
            username=user.username,
            first_name=context.user_data['first_name'],
            last_name=context.user_data['last_name'],
            position=context.user_data['position'],
            railway=context.user_data['railway'],
            branch=context.user_data['branch'],
            is_admin=is_admin(user.id)
        )
        session.add(new_user)
        session.commit()
    
    keyboard = []
    if is_admin(user.id):
        keyboard.append([KeyboardButton('👥 Список пользователей')])
        keyboard.append([KeyboardButton('📨 Рассылка')])
    
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True) if keyboard else None
    
    await update.message.reply_text(
        f'Спасибо за регистрацию, {context.user_data["first_name"]}!\n'
        f'Ваши данные:\n'
        f'Имя: {context.user_data["first_name"]}\n'
        f'Фамилия: {context.user_data["last_name"]}\n'
        f'Должность: {context.user_data["position"]}\n'
        f'Дорога: {context.user_data["railway"].value}\n'
        f'Филиал: {context.user_data["branch"]}',
        reply_markup=reply_markup
    )
    
    return ConversationHandler.END

# Админские команды
@admin_required
async def list_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    with Session() as session:
        users = session.query(User).all()
        
        if not users:
            await update.message.reply_text('Пользователей пока нет.')
            return
        
        message = "Список пользователей:\n\n"
        for user in users:
            status = '👑 Админ' if user.is_admin else '👤 Пользователь'
            message += f"{status} | {user.first_name} {user.last_name}\n"
            if user.username:
                message += f"@{user.username}\n"
            message += f"Должность: {user.position}\n"
            message += f"Дорога: {user.railway.value}\n"
            message += f"Филиал: {user.branch}\n"
            message += f"ID: {user.telegram_id}\n\n"
        
        await update.message.reply_text(message)

# Обработчики рассылки
@admin_required
async def start_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало процесса рассылки"""
    keyboard = [
        [InlineKeyboardButton("🌐 Всем пользователям", callback_data="broadcast_all")],
        [InlineKeyboardButton("🚂 По дороге", callback_data="broadcast_railway")],
        [InlineKeyboardButton("🏢 По филиалу", callback_data="broadcast_branch")],
        [InlineKeyboardButton("❌ Отмена", callback_data="cancel")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        'Выберите целевую аудиторию для рассылки:',
        reply_markup=reply_markup
    )
    return BROADCAST_CHOOSE_TARGET

async def handle_broadcast_target(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка выбора целевой аудитории"""
    query = update.callback_query
    await query.answer()
    
    print(f"Получен callback: {query.data}")  # Отладочная информация
    
    if query.data == 'cancel':
        await query.edit_message_text('Рассылка отменена.')
        return ConversationHandler.END
    
    target_type = query.data.split('_')[1]
    context.user_data['broadcast_target'] = target_type
    print(f"Тип цели: {target_type}")  # Отладочная информация
    
    if target_type == 'all':
        with Session() as session:
            user_count = session.query(User).filter(User.is_active == True).count()
            await query.edit_message_text(
                f'Будет отправлено {user_count} пользователям.\n\n'
                'Введите сообщение для рассылки:'
            )
        return BROADCAST_ENTER_MESSAGE
    
    elif target_type == 'railway':
        print("Формирование списка дорог")  # Отладочная информация
        keyboard = []
        for railway in Railway:
            with Session() as session:
                user_count = session.query(User).filter(
                    User.railway == railway,
                    User.is_active == True
                ).count()
                print(f"Дорога {railway.value}: {user_count} пользователей")  # Отладочная информация
                if user_count > 0:
                    keyboard.append([InlineKeyboardButton(
                        f"{railway.value} ({user_count} польз.)", 
                        callback_data=f"railway_{railway.name}"
                    )])
        
        keyboard.append([InlineKeyboardButton("❌ Отмена", callback_data="cancel")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            'Выберите дорогу для рассылки:',
            reply_markup=reply_markup
        )
        print("Отправлено меню выбора дороги")  # Отладочная информация
        return BROADCAST_CHOOSE_TARGET
    
    elif target_type == 'branch':
        with Session() as session:
            # Получаем все филиалы с количеством пользователей
            branches = session.query(
                User.branch, 
                func.count(User.id).label('user_count')
            ).filter(
                User.is_active == True
            ).group_by(User.branch).all()
            
            keyboard = []
            for branch, count in branches:
                if branch:  # Проверяем, что филиал не пустой
                    keyboard.append([InlineKeyboardButton(
                        f"{branch} ({count} польз.)", 
                        callback_data=f"branch_{branch}"
                    )])
            
            keyboard.append([InlineKeyboardButton("❌ Отмена", callback_data="cancel")])
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                'Выберите филиал для рассылки:',
                reply_markup=reply_markup
            )
            return BROADCAST_CHOOSE_TARGET

async def handle_broadcast_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка выбора конкретной дороги или филиала"""
    query = update.callback_query
    await query.answer()
    
    print(f"Получен callback выбора: {query.data}")  # Отладочная информация
    
    if query.data == 'cancel':
        await query.edit_message_text('Рассылка отменена.')
        return ConversationHandler.END
    
    selection_data = query.data.split('_')
    if len(selection_data) < 2:
        await query.edit_message_text('Произошла ошибка. Попробуйте начать рассылку заново.')
        return ConversationHandler.END
    
    selection_type = selection_data[0]
    selection_value = '_'.join(selection_data[1:])
    print(f"Тип: {selection_type}, Значение: {selection_value}")  # Отладочная информация
    
    context.user_data['broadcast_selection'] = {
        'type': selection_type,
        'value': selection_value
    }
    
    # Получаем количество пользователей для выбранной аудитории
    with Session() as session:
        if selection_type == 'railway':
            railway_enum = getattr(Railway, selection_value)
            user_count = session.query(User).filter(
                User.railway == railway_enum,
                User.is_active == True
            ).count()
            print(f"Найдено пользователей: {user_count}")  # Отладочная информация
        else:  # branch
            user_count = session.query(User).filter(
                User.branch == selection_value,
                User.is_active == True
            ).count()
    
    await query.edit_message_text(
        f'Будет отправлено {user_count} пользователям.\n\n'
        'Введите сообщение для рассылки:'
    )
    return BROADCAST_ENTER_MESSAGE

async def send_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отправка сообщения выбранным пользователям"""
    message_text = update.message.text
    target_type = context.user_data.get('broadcast_target')
    selection = context.user_data.get('broadcast_selection', {})
    
    with Session() as session:
        if target_type == 'all':
            users = session.query(User).filter(User.is_active == True).all()
        elif selection.get('type') == 'railway':
            railway_enum = getattr(Railway, selection['value'])
            users = session.query(User).filter(
                User.railway == railway_enum,
                User.is_active == True
            ).all()
        elif selection.get('type') == 'branch':
            users = session.query(User).filter(
                User.branch == selection['value'],
                User.is_active == True
            ).all()
        else:
            await update.message.reply_text('Произошла ошибка. Попробуйте начать рассылку заново.')
            return ConversationHandler.END
        
        success_count = 0
        fail_count = 0
        
        for user in users:
            try:
                await context.bot.send_message(
                    chat_id=user.telegram_id,
                    text=message_text
                )
                success_count += 1
            except TelegramError:
                fail_count += 1
        
        total = success_count + fail_count
        await update.message.reply_text(
            f'Рассылка завершена!\n'
            f'Успешно отправлено: {success_count} из {total}\n'
            f'Ошибок: {fail_count}'
        )
    
    return ConversationHandler.END

async def cancel_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отмена процесса рассылки"""
    if update.callback_query:
        await update.callback_query.edit_message_text('Рассылка отменена.')
    else:
        await update.message.reply_text('Рассылка отменена.')
    return ConversationHandler.END

# Обработчик отмены
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = []
    if is_admin(update.effective_user.id):
        keyboard.append([KeyboardButton('👥 Список пользователей')])
        keyboard.append([KeyboardButton('📨 Рассылка')])
    
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True) if keyboard else None
    
    await update.message.reply_text(
        'Операция отменена. Для начала регистрации используйте команду /start',
        reply_markup=reply_markup
    )
    return ConversationHandler.END

# Обработчик текстовых сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    
    if text == '👥 Список пользователей' and is_admin(update.effective_user.id):
        await list_users(update, context)
        return
    
    if text == '📨 Рассылка' and is_admin(update.effective_user.id):
        await start_broadcast(update, context)
        return

def main():
    # Создаем приложение бота
    app = Application.builder().token(os.getenv('BOT_TOKEN')).build()

    # Создаем обработчик регистрации
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start_command)],
        states={
            ENTER_FIRST_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_first_name)],
            ENTER_LAST_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_last_name)],
            ENTER_POSITION: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_position)],
            CHOOSE_RAILWAY: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_railway)],
            ENTER_BRANCH: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_branch)]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    # Создаем обработчик рассылки
    broadcast_handler = ConversationHandler(
        entry_points=[
            CommandHandler('broadcast', start_broadcast),
            MessageHandler(filters.Regex('^📨 Рассылка$'), start_broadcast)
        ],
        states={
            BROADCAST_CHOOSE_TARGET: [
                CallbackQueryHandler(handle_broadcast_target, pattern='^broadcast_'),
                CallbackQueryHandler(handle_broadcast_selection, pattern='^(railway|branch)_')
            ],
            BROADCAST_ENTER_MESSAGE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, send_broadcast)
            ]
        },
        fallbacks=[
            CommandHandler('cancel', cancel_broadcast),
            CallbackQueryHandler(cancel_broadcast, pattern='^cancel$')
        ]
    )

    # Добавляем обработчики
    app.add_handler(conv_handler)
    app.add_handler(broadcast_handler)
    app.add_handler(CommandHandler('users', list_users))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Запускаем бота
    print('Бот запущен...')
    app.run_polling(poll_interval=1.0)

if __name__ == '__main__':
    main()