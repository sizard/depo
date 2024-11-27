from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters
)
from datetime import datetime

from models import User, TrainReception, TrainType, TrainCategory, BlockInTrain
from database import session_scope
from handlers.common import show_main_menu, cancel
from train_blocks import TRAIN_BLOCKS, BLOCK_DESCRIPTIONS, BLOCK_CHECKLIST
from handlers.reports import show_reception_report, handle_export_pdf

# Состояния приёмки
CHOOSE_ACTION, ENTER_TRAIN_NUMBER, CHOOSE_TRAIN_CATEGORY, CHOOSE_TRAIN_TYPE, CHECK_BLOCKS, ENTER_NOTES, VIEW_HISTORY = range(7)

async def start_reception(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало процесса приёмки"""
    keyboard = [
        [KeyboardButton('🆕 Новая приёмка')],
        [KeyboardButton('📋 История приёмок')],
        [KeyboardButton('↩️ Главное меню')]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text(
        '🚂 <b>Приёмка состава</b>\n\n'
        'Выберите действие:',
        reply_markup=reply_markup,
        parse_mode='HTML'
    )
    return CHOOSE_ACTION

async def handle_reception_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка выбора действия с приёмкой"""
    choice = update.message.text.strip()
    
    if choice == '↩️ Главное меню':
        return await show_main_menu(update, context)
    
    if choice == '📋 История приёмок':
        return await show_reception_history(update, context)
    
    if choice == '🆕 Новая приёмка':
        keyboard = [[KeyboardButton('↩️ Отмена')]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(
            '🔢 Введите номер состава:',
            reply_markup=reply_markup
        )
        return ENTER_TRAIN_NUMBER
    
    keyboard = [
        [KeyboardButton('🆕 Новая приёмка')],
        [KeyboardButton('📋 История приёмок')],
        [KeyboardButton('↩️ Главное меню')]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        '⚠️ Пожалуйста, используйте кнопки меню',
        reply_markup=reply_markup
    )
    return CHOOSE_ACTION

async def handle_train_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка ввода номера состава"""
    train_number = update.message.text.strip()
    
    if train_number == '↩️ Отмена':
        return await show_main_menu(update, context)
    
    if len(train_number) < 2:
        await update.message.reply_text(
            '⚠️ Пожалуйста, введите корректный номер состава'
        )
        return ENTER_TRAIN_NUMBER
    
    # Сохраняем номер в контексте
    context.user_data['train_number'] = train_number
    
    # Показываем клавиатуру с категориями составов
    keyboard = [
        [KeyboardButton(TrainCategory.ELEKTRICHKA.value), 
         KeyboardButton(TrainCategory.RAIL_BUS.value)],
        [KeyboardButton('↩️ Отмена')]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text(
        'Выберите категорию состава:',
        reply_markup=reply_markup
    )
    return CHOOSE_TRAIN_CATEGORY

async def handle_train_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка выбора категории состава"""
    category = update.message.text.strip()
    
    if category == '↩️ Отмена':
        return await show_main_menu(update, context)
    
    try:
        train_category = TrainCategory(category)
        context.user_data['train_category'] = train_category  # Сохраняем сам enum, а не его значение
        
        if train_category == TrainCategory.ELEKTRICHKA:
            keyboard = [
                [KeyboardButton(TrainType.EP2D.value), KeyboardButton(TrainType.EP3D.value)],
                [KeyboardButton('↩️ Назад')]
            ]
        else:  # TrainCategory.RAIL_BUS
            keyboard = [
                [KeyboardButton(TrainType.RA1.value), KeyboardButton(TrainType.RA2.value), 
                 KeyboardButton(TrainType.RA3.value)],
                [KeyboardButton('↩️ Назад')]
            ]
        
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(
            'Выберите тип состава:',
            reply_markup=reply_markup
        )
        return CHOOSE_TRAIN_TYPE
        
    except ValueError:
        keyboard = [
            [KeyboardButton(TrainCategory.ELEKTRICHKA.value), 
             KeyboardButton(TrainCategory.RAIL_BUS.value)],
            [KeyboardButton('↩️ Отмена')]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        
        await update.message.reply_text(
            '⚠️ Пожалуйста, выберите категорию состава из предложенных вариантов.',
            reply_markup=reply_markup
        )
        return CHOOSE_TRAIN_CATEGORY

async def handle_train_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка выбора типа состава"""
    type_text = update.message.text.strip()
    
    if type_text == '↩️ Назад':
        # Возвращаемся к выбору категории
        keyboard = [
            [KeyboardButton(TrainCategory.ELEKTRICHKA.value), 
             KeyboardButton(TrainCategory.RAIL_BUS.value)],
            [KeyboardButton('↩️ Отмена')]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(
            'Выберите категорию состава:',
            reply_markup=reply_markup
        )
        return CHOOSE_TRAIN_CATEGORY
    
    try:
        train_type = TrainType(type_text)
        
        # Проверяем соответствие типа категории
        train_category = context.user_data.get('train_category')
        if train_category == TrainCategory.ELEKTRICHKA and train_type not in [TrainType.EP2D, TrainType.EP3D]:
            raise ValueError("Неверный тип для категории Электричка")
        elif train_category == TrainCategory.RAIL_BUS and train_type not in [TrainType.RA1, TrainType.RA2, TrainType.RA3]:
            raise ValueError("Неверный тип для категории Рельсовый автобус")
        
        # Создаем новую приёмку в БД
        with session_scope() as session:
            reception = TrainReception(
                train_number=context.user_data['train_number'],
                train_type=train_type,
                user_id=update.effective_user.id
            )
            session.add(reception)
            session.flush()
            
            # Добавляем блоки для проверки
            blocks = TRAIN_BLOCKS.get(train_type, [])
            for block_number in blocks:
                block = BlockInTrain(
                    reception_id=reception.id,
                    block_number=block_number
                )
                session.add(block)
            
            context.user_data['reception_id'] = reception.id
            context.user_data['current_block_index'] = 0
        
        return await show_next_block(update, context)
        
    except ValueError as e:
        keyboard = []
        train_category = context.user_data.get('train_category')
        if train_category == TrainCategory.ELEKTRICHKA:
            keyboard = [
                [KeyboardButton(TrainType.EP2D.value), KeyboardButton(TrainType.EP3D.value)],
                [KeyboardButton('↩️ Назад')]
            ]
        else:
            keyboard = [
                [KeyboardButton(TrainType.RA1.value), KeyboardButton(TrainType.RA2.value), 
                 KeyboardButton(TrainType.RA3.value)],
                [KeyboardButton('↩️ Назад')]
            ]
        
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(
            '⚠️ Пожалуйста, выберите тип состава из предложенных вариантов.',
            reply_markup=reply_markup
        )
        return CHOOSE_TRAIN_TYPE

async def show_next_block(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает следующий блок для проверки"""
    # Определяем, откуда пришел запрос
    message = update.callback_query.message if update.callback_query else update.message
    
    with session_scope() as session:
        # Получаем текущую приёмку
        reception = session.query(TrainReception).filter(
            TrainReception.id == context.user_data['reception_id']
        ).first()
        
        if not reception:
            await message.reply_text(
                '❌ Ошибка: приёмка не найдена',
                reply_markup=ReplyKeyboardMarkup([[KeyboardButton('↩️ Главное меню')]], 
                                               resize_keyboard=True)
            )
            return ConversationHandler.END
        
        # Получаем следующий непроверенный блок
        block = session.query(BlockInTrain).filter(
            BlockInTrain.reception_id == reception.id,
            BlockInTrain.is_checked == False
        ).first()
        
        if not block:
            # Все блоки проверены
            reception.is_completed = True
            session.commit()
            
            keyboard = [
                [KeyboardButton('🆕 Новая приёмка')],
                [KeyboardButton('📋 История приёмок')],
                [KeyboardButton('↩️ Главное меню')]
            ]
            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            
            await message.reply_text(
                '✅ Приёмка состава завершена!\n'
                'Выберите дальнейшее действие:',
                reply_markup=reply_markup
            )
            return CHOOSE_ACTION
        
        # Показываем информацию о блоке
        block_info = (
            f'🔍 <b>Проверка блока: {block.block_number}</b>\n\n'
            f'📝 Описание:\n{BLOCK_DESCRIPTIONS[block.block_number]}\n\n'
            '✅ Критерии проверки:\n'
        )
        
        for item in BLOCK_CHECKLIST[block.block_number]:
            block_info += f'• {item}\n'
        
        # Создаем клавиатуру для оценки блока
        keyboard = [
            [
                InlineKeyboardButton("✅ Исправен", callback_data=f"block_ok_{block.id}"),
                InlineKeyboardButton("⚠️ Неисправен", callback_data=f"block_fail_{block.id}")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await message.reply_text(
            block_info,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
        return CHECK_BLOCKS

async def handle_block_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка результата проверки блока"""
    query = update.callback_query
    await query.answer()
    
    action, block_id = query.data.split('_')[1:]
    block_id = int(block_id)
    
    with session_scope() as session:
        block = session.query(BlockInTrain).get(block_id)
        if not block:
            await query.message.reply_text('❌ Ошибка: блок не найден')
            return ConversationHandler.END
        
        if action == 'fail':
            # Если блок неисправен, запрашиваем комментарий
            await query.message.reply_text(
                '📝 Опишите неисправность:'
            )
            context.user_data['current_block_id'] = block_id
            return ENTER_NOTES
        else:
            # Если блок исправен, отмечаем и переходим к следующему
            block.is_checked = True
            block.notes = "Исправен"
            return await show_next_block(update, context)

async def handle_block_notes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка комментария о неисправности"""
    notes = update.message.text.strip()
    block_id = context.user_data['current_block_id']
    
    with session_scope() as session:
        block = session.query(BlockInTrain).get(block_id)
        if block:
            block.is_checked = True
            block.notes = notes
    
    return await show_next_block(update, context)

async def show_reception_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать историю приёмок"""
    # Отмечаем, откуда пришел пользователь
    context.user_data['from_main_menu'] = update.message.text == '📋 История приёмок'
    print(f"Opening history from main menu: {context.user_data['from_main_menu']}")  # Отладочный вывод
    
    with session_scope() as session:
        # Получаем последние 10 приёмок пользователя
        receptions = session.query(TrainReception).filter(
            TrainReception.user_id == update.effective_user.id
        ).order_by(TrainReception.created_at.desc()).limit(10).all()
        
        if not receptions:
            keyboard = [
                [KeyboardButton('🆕 Новая приёмка')],
                [KeyboardButton('↩️ Главное меню')]
            ]
            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            await update.message.reply_text(
                '📝 История приёмок пуста.',
                reply_markup=reply_markup
            )
            return CHOOSE_ACTION
        
        # Создаем инлайн-кнопки для каждой приёмки
        keyboard = []
        for reception in receptions:
            status = "✅" if reception.is_completed else "🔄"
            button = InlineKeyboardButton(
                f"{status} {reception.train_type.value} №{reception.train_number} "
                f"({reception.created_at.strftime('%d.%m.%Y %H:%M')})",
                callback_data=f"view_reception_{reception.id}"
            )
            keyboard.append([button])
            print(f"Created button with callback_data: view_reception_{reception.id}")  # Отладочный вывод
        
        # Добавляем кнопку возврата
        keyboard.append([InlineKeyboardButton("↩️ Назад", callback_data="back_to_reception")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "📋 История приёмок\nВыберите приёмку для просмотра:",
            reply_markup=reply_markup
        )
        # Возвращаем соответствующее состояние VIEW_HISTORY
        return 1 if context.user_data.get('from_main_menu') else VIEW_HISTORY

async def handle_history_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка выбора приёмки из истории"""
    query = update.callback_query
    print(f"Received callback query: {query}")  # Отладочный вывод
    print(f"Callback data: {query.data}")  # Отладочный вывод
    
    try:
        await query.answer()
        
        if query.data == "back_to_reception":
            # Возвращаемся к меню
            keyboard = [
                [KeyboardButton('🆕 Новая приёмка')],
                [KeyboardButton('📋 История приёмок')],
                [KeyboardButton('↩️ Главное меню')]
            ]
            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            await query.message.reply_text(
                '🚂 Выберите действие:',
                reply_markup=reply_markup
            )
            # Возвращаем в соответствующее меню в зависимости от источника
            if context.user_data.get('from_main_menu'):
                await show_main_menu(update, context)
                return ConversationHandler.END
            return CHOOSE_ACTION
        
        if query.data.startswith('view_reception_'):
            # Показываем детали выбранной приёмки
            reception_id = int(query.data.split('_')[2])
            print(f"Showing reception with ID: {reception_id}")  # Отладочный вывод
            await show_reception_report(update, context, reception_id)
            # Возвращаем соответствующее состояние VIEW_HISTORY
            return VIEW_HISTORY
        
        if query.data.startswith('export_pdf_'):
            # Обработка экспорта в PDF
            reception_id = int(query.data.split('_')[2])
            print(f"Exporting reception with ID: {reception_id}")  # Отладочный вывод
            await handle_export_pdf(update, context)
            return VIEW_HISTORY
        
        print(f"Unknown callback data: {query.data}")  # Отладочный вывод
        return VIEW_HISTORY
        
    except Exception as e:
        print(f"Error in handle_history_selection: {str(e)}")  # Отладочный вывод
        await query.message.reply_text(
            "❌ Произошла ошибка при обработке запроса.\n"
            "Пожалуйста, попробуйте еще раз или начните новую приёмку."
        )
        return CHOOSE_ACTION

# Обработчик приёмки составов
reception_handler = ConversationHandler(
    entry_points=[MessageHandler(filters.Text(['🚂 Приёмка состава']), start_reception)],
    states={
        CHOOSE_ACTION: [
            MessageHandler(filters.Text(['🆕 Новая приёмка', '📋 История приёмок']), handle_reception_choice),
            MessageHandler(filters.Text(['↩️ Главное меню']), show_main_menu)
        ],
        ENTER_TRAIN_NUMBER: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_train_number)
        ],
        CHOOSE_TRAIN_CATEGORY: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_train_category)
        ],
        CHOOSE_TRAIN_TYPE: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_train_type)
        ],
        CHECK_BLOCKS: [
            CallbackQueryHandler(handle_block_check, pattern=r'^block_(ok|fail)_\d+$'),
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_block_notes)
        ],
        ENTER_NOTES: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_block_notes)
        ],
        VIEW_HISTORY: [
            CallbackQueryHandler(handle_history_selection, pattern=r'^(view_reception_\d+|back_to_reception|export_pdf_\d+)$'),
            MessageHandler(filters.Text(['↩️ Главное меню']), show_main_menu)
        ]
    },
    fallbacks=[
        CommandHandler('cancel', cancel),
        MessageHandler(filters.Text(['↩️ Отмена', '↩️ Назад']), cancel),
        MessageHandler(filters.Text(['↩️ Главное меню']), show_main_menu)
    ],
    allow_reentry=True
)
