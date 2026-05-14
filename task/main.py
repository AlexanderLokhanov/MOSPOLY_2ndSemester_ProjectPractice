import asyncio
from datetime import datetime

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message, CallbackQuery

import database as db
from broadcaster import broadcast_poll
from config import BOT_TOKEN, ADMIN_ID


class AbsenceReason(StatesGroup):
    waiting_for_reason = State()


poll_asked_at: dict[int, datetime] = {}



bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())



@dp.message(Command("start"))
async def cmd_start(message: Message):
    """Регистрирует пользователя при первом обращении."""
    db.add_user(
        chat_id=message.chat.id,
        username=message.from_user.username or "",
        first_name=message.from_user.first_name or "",
    )
    await message.answer(
        "👋 Привет! Я AttendBot.\n\n"
        "Когда преподаватель запустит опрос, ты получишь сообщение и сможешь отметиться одной кнопкой."
    )


@dp.message(Command("poll"))
async def cmd_poll(message: Message):
    """Только для администратора: запускает рассылку опроса."""
    if message.from_user.id != ADMIN_ID:
        await message.answer("⛔ У вас нет прав для этой команды.")
        return

    await message.answer("⏳ Запускаю рассылку...")
    asked_at = datetime.now()

    sent = await broadcast_poll(bot)

    # Запоминаем время опроса для всех текущих пользователей
    for chat_id in db.get_all_chat_ids():
        poll_asked_at[chat_id] = asked_at

    await message.answer(f"✅ Опрос отправлен {sent} студентам.")


@dp.callback_query(F.data == "present_yes")
async def callback_yes(call: CallbackQuery, state: FSMContext):
    """Студент нажал «Да» — сохраняем присутствие."""
    chat_id = call.message.chat.id
    asked_at = poll_asked_at.get(chat_id, datetime.now())

    db.mark_present(chat_id=chat_id, asked_at=asked_at)

    await call.message.edit_text("✅ Отлично! Твоё присутствие отмечено.")
    await call.answer()


@dp.callback_query(F.data == "present_no")
async def callback_no(call: CallbackQuery, state: FSMContext):
    """Студент нажал «Нет» — просим написать причину."""
    await state.set_state(AbsenceReason.waiting_for_reason)
    await call.message.edit_text("❌ Понял. Напиши, пожалуйста, причину отсутствия:")
    await call.answer()


@dp.message(AbsenceReason.waiting_for_reason)
async def receive_reason(message: Message, state: FSMContext):
    """Получаем причину отсутствия и сохраняем её."""
    chat_id = message.chat.id
    reason = message.text
    asked_at = poll_asked_at.get(chat_id, datetime.now())

    db.mark_absent(chat_id=chat_id, reason=reason, asked_at=asked_at)
    await state.clear()

    await message.answer("📝 Причина сохранена. Выздоравливай / до встречи!")

async def main():
    db.init_db()
    print("AttendBot запущен...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())