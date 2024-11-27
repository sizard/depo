from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import os

from models import TrainReception, BlockInTrain
from database import session_scope
from train_blocks import BLOCK_DESCRIPTIONS
from handlers.pdf_generator import generate_reception_pdf

async def show_reception_report(update: Update, context: ContextTypes.DEFAULT_TYPE, reception_id: int = None):
    """Показывает подробный отчет о приёмке состава"""
    if not reception_id and 'reception_id' in context.user_data:
        reception_id = context.user_data['reception_id']
    
    if not reception_id:
        await update.message.reply_text(
            '❌ Ошибка: не найден ID приёмки.\n'
            'Пожалуйста, начните новую приёмку или выберите из истории.'
        )
        return
    
    with session_scope() as session:
        reception = session.query(TrainReception).get(reception_id)
        if not reception:
            await update.message.reply_text('❌ Ошибка: приёмка не найдена')
            return
        
        # Формируем заголовок отчета
        report = (
            f'📋 <b>Отчет о приёмке состава №{reception.train_number}</b>\n\n'
            f'🚂 Тип состава: {reception.train_type.value}\n'
            f'👤 Проверяющий: {reception.user.full_name}\n'
            f'💼 Должность: {reception.user.position}\n'
            f'🏢 Отделение: {reception.user.branch}\n'
            f'📅 Дата: {reception.created_at.strftime("%d.%m.%Y %H:%M")}\n'
            f'🏁 Статус: {"Завершена" if reception.is_completed else "В процессе"}\n\n'
            '📝 <b>Результаты проверки блоков:</b>\n'
        )
        
        # Добавляем информацию о каждом блоке
        for block in reception.blocks:
            status = "✅ Исправен" if block.notes == "Исправен" else "⚠️ Неисправен"
            report += f'\n<b>{block.block_number}</b>: {status}\n'
            if block.notes and block.notes != "Исправен":
                report += f'📝 Замечания: {block.notes}\n'
        
        # Добавляем кнопку для экспорта в PDF (будет реализовано позже)
        keyboard = [[InlineKeyboardButton("📑 Экспорт в PDF", callback_data=f"export_pdf_{reception_id}")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Отправляем отчет
        if hasattr(update, 'callback_query'):
            await update.callback_query.message.reply_text(
                report,
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
        else:
            await update.message.reply_text(
                report,
                reply_markup=reply_markup,
                parse_mode='HTML'
            )

async def handle_export_pdf(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка экспорта отчета в PDF"""
    query = update.callback_query
    await query.answer()
    
    try:
        # Получаем ID приёмки из callback_data
        reception_id = int(query.data.split('_')[2])
        print(f"Generating PDF for reception_id: {reception_id}")
        
        # Генерируем PDF
        filepath = generate_reception_pdf(reception_id)
        print(f"PDF generated at: {filepath}")
        
        # Отправляем файл
        with open(filepath, 'rb') as pdf_file:
            await query.message.reply_document(
                document=pdf_file,
                filename=os.path.basename(filepath),
                caption='📑 Отчет о приёмке состава в формате PDF'
            )
        
        # Удаляем временный файл
        os.remove(filepath)
        print("PDF file sent and removed successfully")
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"❌ Ошибка при экспорте в PDF:\n{error_details}")
        await query.message.reply_text(
            f'❌ Произошла ошибка при создании PDF:\n{str(e)}'
        )
