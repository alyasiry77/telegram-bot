from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import CommandStart, Command
from sqlalchemy.ext.asyncio import AsyncSession
from bot.app.services.user_service import get_user_by_telegram_id, create_user
from bot.app.services.referral_service import process_referral
from bot.app.keyboards.reply import main_menu
from bot.app.config import settings
from bot.app.messages import WELCOME, WELCOME_REFERRAL
import logging

router = Router()
logger = logging.getLogger(__name__)

@router.message(CommandStart())
async def cmd_start(message: Message, session: AsyncSession):
    args = message.text.split(maxsplit=1)
    ref_code = None
    if len(args) > 1:
        ref_code = args[1].strip()

    telegram_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name
    last_name = message.from_user.last_name

    referrer = None
    if ref_code:
        # ref_code can be numeric id or REF123? We support numeric telegram_id or user id
        # Try to parse as telegram_id
        try:
            # If ref_code is like REF123, extract digits
            code_digits = "".join(c for c in ref_code if c.isdigit())
            if code_digits:
                ref_tid = int(code_digits)
                # Search by telegram_id if matches pattern, else try to find user id
                ref_user = await get_user_by_telegram_id(session, ref_tid)
                if ref_user and ref_user.telegram_id != telegram_id:
                    referrer = ref_user
                else:
                    # Try to find by id field if code is user id directly
                    from sqlalchemy import select
                    from bot.app.models.user import User
                    r = await session.execute(select(User).where(User.id == ref_tid))
                    u = r.scalar_one_or_none()
                    if u and u.telegram_id != telegram_id:
                        referrer = u
        except Exception as e:
            logger.warning(f"Referral parse error {e}")

    existing = await get_user_by_telegram_id(session, telegram_id)
    if existing:
        # Already registered - do not count referral again
        is_admin = settings.is_admin(telegram_id)
        await message.answer(
            WELCOME.format(name=message.from_user.first_name or "صديقي"),
            reply_markup=main_menu(is_admin),
            parse_mode="HTML"
        )
        return

    user, is_new = await create_user(session, telegram_id, username, first_name, last_name, referrer)

    # Process referral bonus
    if is_new and referrer:
        # Need to re-fetch referrer fresh for update
        from bot.app.services.user_service import get_user_by_id
        fresh_ref = await get_user_by_id(session, referrer.id)
        try:
            await process_referral(session, user, fresh_ref)
        except Exception as e:
            logger.exception(f"Referral process failed: {e}")
        await message.answer(
            WELCOME_REFERRAL.format(name=first_name or "صديقي"),
            reply_markup=main_menu(settings.is_admin(telegram_id)),
            parse_mode="HTML"
        )
        # Notify referrer
        try:
            await message.bot.send_message(
                referrer.telegram_id,
                f"🎉 <b>إحالة جديدة!</b>\n👤 انضم <b>{first_name}</b> عبر رابطك وحصلت على مكافأة.",
                parse_mode="HTML"
            )
        except:
            pass
        return

    await message.answer(
        WELCOME.format(name=first_name or "صديقي"),
        reply_markup=main_menu(settings.is_admin(telegram_id)),
        parse_mode="HTML"
    )

@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer("ℹ️ استخدم القائمة الرئيسية للتنقل. أرسل /start للبداية.")
