from datetime import datetime
import os
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from models import TrainReception
from database import session_scope

# Регистрируем шрифт Calibri
CALIBRI_PATH = "C:/Windows/Fonts/calibri.ttf"
CALIBRI_BOLD_PATH = "C:/Windows/Fonts/calibrib.ttf"

try:
    pdfmetrics.registerFont(TTFont('Calibri', CALIBRI_PATH))
    pdfmetrics.registerFont(TTFont('Calibri-Bold', CALIBRI_BOLD_PATH))
except:
    print("Не удалось загрузить шрифт Calibri, используем стандартный шрифт")

def generate_reception_pdf(reception_id: int) -> str:
    """Генерирует PDF-отчет о приёмке состава"""
    with session_scope() as session:
        reception = session.query(TrainReception).get(reception_id)
        if not reception:
            raise ValueError("Приёмка не найдена")
        
        # Создаем директорию для отчетов, если её нет
        reports_dir = os.path.join(os.path.dirname(__file__), '..', 'reports')
        os.makedirs(reports_dir, exist_ok=True)
        
        # Формируем имя файла
        filename = f"reception_{reception.train_number}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        filepath = os.path.join(reports_dir, filename)
        
        # Создаем PDF документ
        doc = SimpleDocTemplate(
            filepath,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )
        
        # Создаем стили
        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(
            name='Custom',
            fontName='Calibri',
            fontSize=12,
            leading=14
        ))
        styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=styles['Custom'],
            fontName='Calibri-Bold',
            fontSize=16,
            spaceAfter=30
        ))
        
        # Формируем содержимое документа
        elements = []
        
        # Заголовок
        elements.append(Paragraph(
            f'Отчет о приёмке состава №{reception.train_number}',
            styles['CustomTitle']
        ))
        
        # Основная информация
        info = [
            ['Тип состава:', reception.train_type.value],
            ['Проверяющий:', reception.user.full_name],
            ['Должность:', reception.user.position],
            ['Отделение:', reception.user.branch],
            ['Дата:', reception.created_at.strftime("%d.%m.%Y %H:%M")],
            ['Статус:', 'Завершена' if reception.is_completed else 'В процессе']
        ]
        
        info_table = Table(info, colWidths=[3*inch, 3*inch])
        info_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Calibri'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('PADDING', (0, 0), (-1, -1), 6)
        ]))
        elements.append(info_table)
        elements.append(Spacer(1, 20))
        
        # Результаты проверки блоков
        elements.append(Paragraph('Результаты проверки блоков:', styles['Custom']))
        elements.append(Spacer(1, 10))
        
        blocks_data = []
        for block in reception.blocks:
            status = "✓ Исправен" if block.notes == "Исправен" else "⚠ Неисправен"
            row = [block.block_number, status]
            blocks_data.append(row)
            if block.notes and block.notes != "Исправен":
                blocks_data.append(['Замечания:', block.notes])
        
        if blocks_data:
            blocks_table = Table(blocks_data, colWidths=[3*inch, 3*inch])
            blocks_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), 'Calibri'),
                ('FONTSIZE', (0, 0), (-1, -1), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
                ('PADDING', (0, 0), (-1, -1), 6)
            ]))
            elements.append(blocks_table)
        
        # Генерируем PDF
        doc.build(elements)
        return filepath
