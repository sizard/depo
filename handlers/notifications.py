from telegram.ext import ContextTypes
from models import User, UserRole
from database import session_scope

async def notify_admins(context: ContextTypes.DEFAULT_TYPE, message: str):
    """Отправка уведомления всем администраторам"""
    with session_scope() as session:
        admins = session.query(User).filter(User.role == UserRole.ADMIN).all()
        
        for admin in admins:
            try:
                await context.bot.send_message(
                    chat_id=admin.id,
                    text=message,
                    parse_mode='HTML'
                )
            except Exception as e:
                print(f"Ошибка отправки уведомления админу {admin.id}: {e}")
