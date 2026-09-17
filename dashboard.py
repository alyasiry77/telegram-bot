from fastapi import FastAPI, Depends, HTTPException, Request, Query
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from bot.app.database.engine import async_session
from bot.app.models.user import User
from bot.app.models.withdrawal import Withdrawal
from bot.app.models.campaign import Campaign
from bot.app.config import settings
import os
import hashlib
import hmac

app = FastAPI(title="Earning Platform Admin Dashboard")

async def get_session():
    async with async_session() as s:
        yield s

def require_admin(request: Request):
    token = request.headers.get("X-Admin-Token") or request.query_params.get("token")
    # Simple: check if token equals BOT_TOKEN prefix or ADMIN_IDS
    if token != settings.secret_key and token not in str(settings.admin_ids):
        # Allow if ADMIN_IDS header matches one
        raise HTTPException(401, "Unauthorized")
    return True

@app.get("/health")
async def health(session: AsyncSession = Depends(get_session)):
    try:
        cnt = (await session.execute(select(func.count(User.id)))).scalar_one()
        return {"status": "ok", "users": cnt}
    except Exception as e:
        return JSONResponse({"status": "error", "error": str(e)}, status_code=500)

@app.get("/api/stats", dependencies=[Depends(require_admin)])
async def stats(session: AsyncSession = Depends(get_session)):
    from bot.app.services.stats_service import get_dashboard_stats
    return await get_dashboard_stats(session)

@app.get("/api/users", dependencies=[Depends(require_admin)])
async def users_list(limit: int = 20, session: AsyncSession = Depends(get_session)):
    res = await session.execute(select(User).order_by(User.created_at.desc()).limit(limit))
    return [{"id": u.telegram_id, "name": u.full_name, "balance": u.balance, "refs": u.referral_count} for u in res.scalars().all()]

@app.get("/api/offerwall/postback")
async def offerwall_postback(user_id: int, offer_id: str, signature: str = Query(""), session: AsyncSession = Depends(get_session)):
    # Validate signature = hmac(secret, user_id:offer_id)
    expected = hmac.new(settings.secret_key.encode(), f"{user_id}:{offer_id}".encode(), hashlib.sha256).hexdigest()[:16]
    if signature and signature != expected:
        raise HTTPException(400, "Invalid signature")
    # Credit user (mock: find by telegram_id == user_id)
    from sqlalchemy import select as sel
    u = (await session.execute(sel(User).where(User.telegram_id == user_id))).scalar_one_or_none()
    if not u:
        raise HTTPException(404, "User not found")
    from bot.app.services.financial_service import credit
    await credit(session, u, 30, "offerwall", f"Offer {offer_id}", reference_type="offerwall", reference_id=offer_id)
    return {"status": "ok", "credited": 30}

@app.get("/webapp", response_class=HTMLResponse)
async def webapp():
    try:
        with open("web/static/app.html", encoding="utf-8") as f:
            return HTMLResponse(f.read())
    except:
        return HTMLResponse("<h1>WebApp not found</h1>", status_code=404)

@app.get("/", response_class=HTMLResponse)
async def index():
    return """
    <html dir="rtl"><head><meta charset="utf-8"><title>Dashboard</title>
    <style>body{font-family:system-ui;padding:20px} .card{border:1px solid #ddd;padding:15px;border-radius:8px;margin:10px 0}</style>
    </head><body>
    <h1>📊 لوحة تحكم المنصة</h1>
    <div class="card"><a href="/health">/health</a> - فحص الصحة</div>
    <div class="card"><a href="/api/stats?token=YOUR_SECRET">/api/stats</a> - الإحصائيات (header X-Admin-Token)</div>
    <div class="card"><a href="/api/users?token=YOUR_SECRET">/api/users</a> - المستخدمون</div>
    <div class="card"><a href="/webapp">/webapp</a> - لوحة الويب (Telegram WebApp)</div>
    <div class="card"><a href="/api/offerwall/postback?user_id=123&offer_id=test&signature=xxx">/api/offerwall/postback</a> - Offerwall</div>
    <p>شغّل: <code>uvicorn web.dashboard:app --port 0.0.0.0 --port 8000 --reload</code></p>
    </body></html>
    """

# To run: uvicorn web.dashboard:app --host 0.0.0.0 --port 8000 --reload
try:
    app.mount("/static", StaticFiles(directory="web/static"), name="static")
except:
    pass
