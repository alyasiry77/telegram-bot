import time
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery

class ThrottlingMiddleware(BaseMiddleware):
    def __init__(self, rate: float = 0.5):
        self.rate = rate
        self.last: dict[int, float] = {}

    async def __call__(self, handler: Callable, event: TelegramObject, data: Dict[str, Any]) -> Any:
        user_id = None
        if hasattr(event, "from_user") and event.from_user:
            user_id = event.from_user.id
        if user_id:
            now = time.time()
            last = self.last.get(user_id, 0)
            if now - last < self.rate:
                if isinstance(event, CallbackQuery):
                    await event.answer("⏳ تمهل قليلاً...", show_alert=False)
                return
            self.last[user_id] = now
        return await handler(event, data)
