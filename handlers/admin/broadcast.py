import asyncio
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from data_base.models import ADMIN_ID, User
from data_base.db import SessionLocal
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError

router = Router()


@router.message(Command("sendmessage"))
async def send_message_to_all(message: Message):
    if message.from_user.id not in ADMIN_ID:
        return

    photo_file_id = None
    text = None

    if message.photo:
        # Админ прислал фото (возможно, с подписью)
        photo_file_id = message.photo[-1].file_id  # последний элемент — самое высокое разрешение
        text = message.caption or ""
    else:
        # Обычный текст: команда + текст рассылки
        text = message.text.replace("/sendmessage", "", 1).strip()

    if not text and not photo_file_id:
        await message.answer(
            "Использование:\n"
            "/sendmessage <текст> — просто текст\n"
            "Или отправьте фото с подписью, начинающейся на /sendmessage"
        )
        return

    # Если это фото, но подпись не начиналась с команды — тоже нужно проверить
    if photo_file_id and not (message.caption or "").startswith("/sendmessage"):
        return  # это фото не для рассылки, а что-то другое — игнорируем

    if photo_file_id:
        text = text.replace("/sendmessage", "", 1).strip()

    with SessionLocal() as session:
        users = session.query(User).filter_by(is_blocked=False).all()
        telegram_ids = [u.telegram_id for u in users]

    await message.answer(f"Начинаю рассылку {len(telegram_ids)} пользователям...")

    sent = 0
    blocked = 0
    failed = 0
    newly_blocked_ids = []

    for telegram_id in telegram_ids:
        try:
            if photo_file_id:
                await message.bot.send_photo(telegram_id, photo=photo_file_id, caption=text or None)
            else:
                await message.bot.send_message(telegram_id, text)
            sent += 1
        except TelegramForbiddenError:
            blocked += 1
            newly_blocked_ids.append(telegram_id)
        except TelegramBadRequest:
            failed += 1
        except Exception:
            failed += 1

        await asyncio.sleep(0.05)

    if newly_blocked_ids:
        with SessionLocal() as session:
            session.query(User).filter(User.telegram_id.in_(newly_blocked_ids)).update(
                {"is_blocked": True}, synchronize_session=False
            )
            session.commit()

    await message.answer(
        f"✅ Рассылка завершена.\n"
        f"Доставлено: {sent}\n"
        f"Заблокировали бота: {blocked}\n"
        f"Другие ошибки: {failed}"
    )