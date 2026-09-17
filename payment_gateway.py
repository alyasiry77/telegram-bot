"""
Mock gateway for TON/USDT auto-payout.
Replace `send_payout` with real API (Tonkeeper, NowPayments, etc.)
"""
import logging
import random
logger = logging.getLogger(__name__)

async def send_payout(method: str, account: str, amount_usd: float, withdrawal_id: int) -> tuple[bool, str]:
    # In production: call external API here
    logger.info(f"[GATEWAY] {method} payout ${amount_usd:.2f} to {account} wd#{withdrawal_id}")
    # Simulate 90% success
    if random.random() < 0.9:
        tx = f"tx_{withdrawal_id}_{random.randint(1000,9999)}"
        return True, tx
    return False, "gateway_error: insufficient funds or invalid address"

async def validate_address(method: str, account: str) -> tuple[bool, str]:
    if len(account) < 5:
        return False, "عنوان قصير"
    if method == "ton" and not (account.startswith("EQ") or account.startswith("UQ")):
        # relax for demo
        pass
    if method == "crypto" and len(account) < 10:
        return False, "عنوان كريبتو غير صالح"
    return True, "ok"
