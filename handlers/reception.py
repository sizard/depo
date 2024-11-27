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

from models import User, TrainReception, TrainType, BlockInTrain
from database import session_scope
from handlers.common import show_main_menu, cancel
from train_blocks import TRAIN_BLOCKS, BLOCK_DESCRIPTIONS, BLOCK_CHECKLIST
from handlers.reports import show_reception_report, handle_export_pdf

# Состояния приёмки
CHOOSE_ACTION, ENTER_TRAIN_NUMBER, CHOOSE_TRAIN_TYPE, CHECK_BLOCKS, ENTER_NOTES = range(5)

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
    """Обработка выбора действия"""
    choice = update.message.text
    
    if choice == '🆕 Новая приёмка':
        await update.message.reply_text(
            '🔢 Введите номер состава:'
        )
        return ENTER_TRAIN_NUMBER
    elif choice == '📋 История приёмок':
        return await show_reception_history(update, context)
    elif choice == '↩️ Главное меню':
        return await show_main_menu(update, context)
    else:
        await update.message.reply_text(
            '⚠️ Пожалуйста, используйте кнопки меню.'
        )
        return CHOOSE_ACTION

async def handle_train_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка ввода номера состава"""
    train_number = update.message.text.strip()
    
    # Проверяем формат номера
    if not train_number.isdigit():
        await update.message.reply_text(
            '⚠️ Номер состава должен содержать только цифры.\n'
            '🔄 Попробуйте еще раз:'
        )
        return ENTER_TRAIN_NUMBER
    
    # Сохраняем номер в контексте
    context.user_data['train_number'] = train_number
    
    # Показываем клавиатуру с типами составов
    keyboard = [
        [KeyboardButton('🚅 Электричка')],
        [KeyboardButton('🚂 Рельсовый автобус')],
        [KeyboardButton('↩️ Отмена')]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text(
        '🚂 Выберите тип состава:',
        reply_markup=reply_markup
    )
    return CHOOSE_TRAIN_TYPE

async def handle_train_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка выбора типа состава"""
    type_text = update.message.text.strip()
    
    if type_text == '↩️ Отмена':
        return await show_main_menu(update, context)
    
    # Определяем тип состава
    train_type = None
    if type_text == '🚅 Электричка':
        train_type = TrainType.ELEKTRICHKA
    elif type_text == '🚂 Рельсовый автобус':
        train_type = TrainType.RAIL_BUS
    else:
        await update.message.reply_text(
            '⚠️ Пожалуйста, выберите тип состава из предложенных вариантов.'
        )
        return CHOOSE_TRAIN_TYPE
    
    # Создаем новую приёмку
    try:
        with session_scope() as session:
            user = session.query(User).filter(User.id == update.effective_user.id).first()
            if not user:
                await update.message.reply_text('❌ Ошибка: пользователь не найден')
                return ConversationHandler.END
            
            reception = TrainReception(
                train_number=context.user_data['train_number'],
                train_type=train_type,
                user_id=user.id,
                created_at=datetime.now(),
                is_completed=False
            )
            session.add(reception)
            session.flush()  # Получаем ID приёмки
            
            # Создаем блоки для проверки
            for block_name in TRAIN_BLOCKS[train_type]:
                block = BlockInTrain(
                    reception_id=reception.id,
                    block_number=block_name,
                    is_checked=False
                )
                session.add(block)
            
            # Сохраняем ID приёмки в контексте
            context.user_data['reception_id'] = reception.id
            
            # Получаем первый блок для проверки
            block = session.query(BlockInTrain).filter(
                BlockInTrain.reception_id == reception.id,
                BlockInTrain.is_checked == False
            ).first()
            
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
            
            await update.message.reply_text(
                block_info,
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
            return CHECK_BLOCKS
            
    except Exception as e:
        print(f"❌ Ошибка при создании приёмки: {str(e)}")
        await update.message.reply_text(
            '❌ Произошла ошибка при создании приёмки.\n'
            '🔄 Пожалуйста, попробуйте еще раз позже.'
        )
        return ConversationHandler.END

async def show_next_block(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает следующий блок для проверки"""
    with session_scope() as session:
        # Получаем следующий непроверенный блок
        block = session.query(BlockInTrain).filter(
            BlockInTrain.reception_id == context.user_data['reception_id'],
            BlockInTrain.is_checked == False
        ).first()
        
        if not block:
            # Все блоки проверены
            reception = session.query(TrainReception).get(context.user_data['reception_id'])
            reception.is_completed = True
            
            message_text = (
                '✅ Приёмка состава завершена!\n\n'
                f'🚂 Состав №{reception.train_number}\n'
                f'📅 Дата: {reception.created_at.strftime("%d.%m.%Y %H:%M")}\n'
                '🏁 Статус: Завершена\n\n'
                '📋 Сейчас я покажу вам подробный отчет...'
            )
            
            if hasattr(update, 'callback_query'):
                await update.callback_query.message.reply_text(message_text)
            else:
                await update.message.reply_text(message_text)
            
            # Показываем подробный отчет
            from handlers.reports import show_reception_report
            await show_reception_report(update, context)
            return ConversationHandler.END
        
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
        
        if hasattr(update, 'callback_query'):
            await update.callback_query.message.reply_text(
                block_info,
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
        else:
            await update.message.reply_text(
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
    """Показывает историю приёмок пользователя"""
    with session_scope() as session:
        # Получаем последние 10 приёмок пользователя
        receptions = session.query(TrainReception)\
            .filter(TrainReception.user_id == update.effective_user.id)\
            .order_by(TrainReception.created_at.desc())\
            .limit(10)\
            .all()
        
        if not receptions:
            await update.message.reply_text(
                '📋 История приёмок пуста.\n'
                'Начните новую приёмку!'
            )
            return await start_reception(update, context)
        
        # Создаем клавиатуру с кнопками для каждой приёмки
        keyboard = []
        for reception in receptions:
            status = "✅" if reception.is_completed else "🔄"
            button_text = f"{status} Состав №{reception.train_number} ({reception.created_at.strftime('%d.%m.%Y')})"
            keyboard.append([InlineKeyboardButton(button_text, callback_data=f"view_reception_{reception.id}")])
        
        keyboard.append([InlineKeyboardButton("↩️ Назад", callback_data="back_to_reception")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            '📋 <b>История приёмок</b>\n\n'
            'Выберите приёмку для просмотра отчета:',
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
        return CHECK_BLOCKS

async def handle_history_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка выбора приёмки из истории"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "back_to_reception":
        return await start_reception(update, context)
    
    reception_id = int(query.data.split('_')[2])
    from handlers.reports import show_reception_report
    await show_reception_report(update, context, reception_id)
    return CHECK_BLOCKS

# Создаем обработчик для приёмки
reception_handler = ConversationHandler(
    entry_points=[MessageHandler(filters.Text(['🚂 Приёмка состава']), start_reception)],
    states={
        CHOOSE_ACTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_reception_choice)],
        ENTER_TRAIN_NUMBER: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_train_number)],
        CHOOSE_TRAIN_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_train_type)],
        CHECK_BLOCKS: [
            CallbackQueryHandler(handle_block_check, pattern=r'^block_(ok|fail)_\d+$'),
            CallbackQueryHandler(handle_history_selection, pattern=r'^view_reception_\d+$'),
            CallbackQueryHandler(handle_history_selection, pattern=r'^back_to_reception$'),
            CallbackQueryHandler(handle_export_pdf, pattern=r'^export_pdf_\d+$')
        ],
        ENTER_NOTES: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_block_notes)],
    },
    fallbacks=[
        CommandHandler('cancel', cancel),
        MessageHandler(filters.Text(['↩️ Главное меню']), show_main_menu)
    ]
)
