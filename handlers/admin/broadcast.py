import asyncio
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message
from data_base.models import ADMIN_ID, User
from data_base.db import SessionLocal
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError

router = Router()


def is_sendmessage_command(message: Message) -> bool:
    text = message.text or message.caption or ""
    return text.startswith("/sendmessage")


@router.message(F.func(is_sendmessage_command))
async def send_message_to_all(message: Message):
    if message.from_user.id not in ADMIN_ID:
        return

    if message.photo:
        photo_file_id = message.photo[-1].file_id
        raw_text = message.caption or ""
    else:
        photo_file_id = None
        raw_text = message.text or ""

    text = raw_text.replace("/sendmessage", "", 1).strip()

    if not text and not photo_file_id:
        await message.answer("Использование: /sendmessage <текст>, или фото с подписью /sendmessage <текст>")
        return

    with SessionLocal() as session:
        users = session.query(User).all()
        telegram_ids = [u.telegram_id for u in users]

    await message.answer(f"Начинаю рассылку {len(telegram_ids)} пользователям...")

    sent = 0
    blocked = 0
    failed = 0

    for telegram_id in telegram_ids:
        try:
            if photo_file_id:
                await message.bot.send_photo(telegram_id, photo=photo_file_id, caption=text or None)
            else:
                await message.bot.send_message(telegram_id, text)
            sent += 1
        except TelegramForbiddenError:
            blocked += 1
        except TelegramBadRequest:
            failed += 1
        except Exception:
            failed += 1

        await asyncio.sleep(0.05)

    await message.answer(
        f"✅ Рассылка завершена.\nДоставлено: {sent}\nЗаблокировали бота: {blocked}\nДругие ошибки: {failed}"
    )