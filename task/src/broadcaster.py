from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from task.src.database import get_all_chat_ids


def build_poll_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Да ✅", callback_data="present_yes"),
            InlineKeyboardButton(text="Нет ❌", callback_data="present_no"),
        ]
    ])


async def broadcast_poll(bot: Bot):
    """Рассылает вопрос о посещаемости всем пользователям."""
    chat_ids = get_all_chat_ids()
    sent = 0
    for chat_id in chat_ids:
        try:
            await bot.send_message(
                chat_id=chat_id,
                text="📋 <b>Отметка посещаемости</b>\n\nВы сейчас на паре?",
                parse_mode="HTML",
                reply_markup=build_poll_keyboard(),
            )
            sent += 1
        except Exception:
            # Пользователь мог заблокировать бота — просто пропускаем
            pass
    return sent
