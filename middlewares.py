from typing import Any, Awaitable, Callable, Dict, Set
from aiogram import BaseMiddleware
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, TelegramObject

from database import db_get_user
from config import TEXTS

REGISTERED_USERS_CACHE: Set[int] = set()

class RegistrationCheckMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        user_id = None

        if isinstance(event, Message):
            user_id = event.from_user.id if event.from_user else None
            text = event.text or ""
            if text.startswith("/start") or text.startswith("/simsim") or text.startswith("/admin"):
                return await handler(event, data)

        elif isinstance(event, CallbackQuery):
            user_id = event.from_user.id
            if event.data and (
                event.data.startswith("set_lang:") or event.data.startswith("reg_city:")
            ):
                return await handler(event, data)

        state: FSMContext = data.get("state")
        if state:
            current_state = await state.get_state()
            if current_state and (
                current_state.startswith("Registration") or current_state.startswith("Admin")
            ):
                return await handler(event, data)

        if user_id:
            if user_id in REGISTERED_USERS_CACHE:
                return await handler(event, data)

            user = await db_get_user(user_id)
            if not user:
                if isinstance(event, Message):
                    await event.answer(TEXTS["ru"]["not_registered"])
                elif isinstance(event, CallbackQuery):
                    await event.answer("⛔ Сначала зарегистрируйтесь! Отправьте /start", show_alert=True)
                return
            else:
                REGISTERED_USERS_CACHE.add(user_id)

        return await handler(event, data)
