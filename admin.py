from aiogram.filters import BaseFilter
from aiogram.types import Message, CallbackQuery
from bot.app.config import settings

class AdminFilter(BaseFilter):
    async def __call__(self, event: Message | CallbackQuery) -> bool:
        user_id = event.from_user.id if event.from_user else 0
        return settings.is_admin(user_id)
