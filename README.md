# Telegram Earning Platform - منصة الربح من تيليجرام

منصة ربحية متكاملة Production-Ready مبنية بـ **Python 3.11 + aiogram 3.x + SQLAlchemy Async + PostgreSQL**

## 🌟 المميزات
- ✅ تسجيل تلقائي + إحالات مع منع التلاعب
- ✅ مكافأة يومية (5 نقاط) + مهمة يومية (10 نقاط) مع قفل 24ساعة
- ✅ نظام مهام (اشتراك قناة مع تحقق Telegram API)
- ✅ مهام مدفوعة (حملات معلنين)
- ✅ نظام مالي Ledger حقيقي (Transaction) مع أقفال وحماية Race Condition
- ✅ سحب أرباح مع حد أدنى وموافقة إدارة
- ✅ لوحة إدارة داخل تيليجرام محمية بـ ADMIN_IDS
- ✅ إحصائيات + إذاعة + دعم فني + إعلانات
- ✅ Settings قابلة للتعديل من الإدارة (بدون Hardcoded)
- ✅ Anti-Fraud, Audit Logs, Rate Limiting
- ✅ Persistence بعد Restart (PostgreSQL)

---

## 🏗️ Architecture

```
User -> Telegram API -> aiogram Dispatcher -> Middleware (Throttling + Maintenance + DB Session)
        -> Handlers -> Services (Business Logic) -> SQLAlchemy -> PostgreSQL
                                                  -> Ledger (Transactions)
Admin -> Filter(AdminFilter) -> Admin Handlers -> Same Services
```

**الطبقات:**
- `handlers/` : استقبال الرسائل والأزرار
- `services/` : المنطق التجاري (financial, referral, reward, tasks, withdrawal, stats)
- `models/` : جداول DB
- `keyboards/` : أزرار Reply + Inline
- `middlewares/` : حماية وصيانة
- `states/` : حالات FSM للمحادثات متعددة الخطوات
- `utils/` : مساعدات

**Flow الرئيسي:**
1. `/start` → إنشاء User + ربط Referral → إرسال القائمة
2. `Daily Reward` → تحقق 24h → credit via Ledger → تحديث last_daily_reward
3. `Task` → عرض → تحقق اشتراك (getChatMember) → TaskCompletion + credit (ذري مع FOR UPDATE)
4. `Campaign` → Advertiser ينشئ (FSM) → pending → Admin يوافق → active → users ينفذون
5. `Withdrawal` → FSM (method/account/amount) → reserve balance → pending → Admin (approve/paid/reject+refund)

---

## 📂 هيكل المشروع

```
bot/
├── app/
│   ├── handlers/ (start, menu, daily, tasks, paid_tasks, withdrawal, advertiser, support, admin)
│   ├── keyboards/ (reply.py, inline.py)
│   ├── middlewares/ (user, throttling)
│   ├── services/ (user, referral, reward, task, financial, withdrawal, stats, settings)
│   ├── database/ (engine.py)
│   ├── models/ (user, task, campaign, transaction, withdrawal, advertisement, support, admin_log, settings)
│   ├── states/ (campaign.py - FSM)
│   ├── filters/ (admin.py)
│   ├── utils/ (helpers.py)
│   ├── config.py
│   ├── messages.py
│   └── bot.py
├── migrations/
├── tests/
├── main.py
├── requirements.txt
├── .env.example
├── Dockerfile
└── docker-compose.yml
```

وظيفة كل مجلد مشروحة أعلاه. فصل واضح بين Handlers/DB/Business/Keyboards/Services/Config.

---

## 🗄️ Database Schema (PostgreSQL/SQLite)

**users** (id, telegram_id UNIQUE, username, first_name, balance, total_earnings, referral_count, level, is_banned, referrer_id FK, last_daily_reward, created_at...)

**transactions** (id, user_id FK, type, amount, balance_after, description, status, reference_type/id, extra_data JSON, created_at) - **Ledger**

**tasks** (id, title, url, type, reward_points, max_completions, current_completions, status, channel_username...)

**task_completions** (id, user_id, task_id UNIQUE(user,task), reward_points)

**campaigns** (id, advertiser_id FK, title, url, required_completions, reward_per_user, total_budget, platform_fee_percent, status pending/active...)

**campaign_completions** (user_id, campaign_id UNIQUE)

**withdrawals** (id, user_id, amount_points, fee, net, method, account_info, status pending/approved/paid/rejected...)

**advertisements**, **support_tickets**, **admin_logs**, **settings** (key/value)

كل جدول له PK و FK و Indexes.

---

## 💰 نظام النقاط والأرباح

- `points_to_cash = 0.01` → 100 نقطة = 1$
- كل عملية مالية تسجل في `transactions` مع `balance_after`، ولا يُعتمد على `balance +=` فقط.
- `SELECT ... FOR UPDATE` لمنع Race Condition.
- Idempotency عبر `reference_type/reference_id` (مثال: daily_reward + timestamp, task#id, referral#user_id)
- رسوم سحب قابلة للتعديل `withdrawal_fee_percent`
- ربح المنصة = `campaign_profit_percent` (افتراضي 30%)

القيم **قابلة للتعديل من Admin** عبر `/set key value` أو DB settings.

---

## 🛡️ الحماية

- منع تكرار الحساب (telegram_id UNIQUE)
- منع إحالة ذاتية ومكررة (فحص reference + referrer_id)
- منع تنفيذ مهمة مرتين (UNIQUE + check)
- تحقق اشتراك عبر `getChatMember` (لا يمنح قبل التحقق)
- حماية Admin بـ `AdminFilter` + `ADMIN_IDS`
- Rate Limiting (ThrottlingMiddleware)
- Validation لكل مدخل
- SQL Injection محمي عبر ORM
- Audit Logs لكل إجراء إداري ومالي
- Financial Locks + Ledger

---

## 🚀 التثبيت والتشغيل

### 1) إنشاء بوت عبر BotFather
- افتح `@BotFather` في تيليجرام
- أرسل `/newbot` → اختر اسم → اختر username → ستحصل على `BOT_TOKEN`
- (اختياري) `/setdescription` و `/setabouttext`
- أنشئ قناة واحصل على `@channel_username`

### 2) إعداد المشروع محلياً

```bash
git clone <repo>
cd "Telegram Earning Platform"
python -m venv venv
# Windows
venv\Scripts\activate
# Linux
source venv/bin/activate

pip install -r requirements.txt

cp .env.example .env
# عدّل .env وضع BOT_TOKEN و ADMIN_IDS (معرفك من @userinfobot)
```

### 3) قاعدة البيانات

**خيار A: SQLite (تطوير سريع)**
```env
DATABASE_URL=sqlite+aiosqlite:///./bot.db
```
سيتم إنشاء الجداول تلقائياً عند أول تشغيل (`init_db()`).

**خيار B: PostgreSQL (Production)**
```bash
# عبر Docker
docker-compose up -d db
# أو يدوياً
createdb telegram_earning
# ثم في .env:
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/telegram_earning

# Migrations
alembic upgrade head
# أو لإنشاء migration جديد:
alembic revision --autogenerate -m "init"
alembic upgrade head
```

### 4) التشغيل محلياً

```bash
python main.py
# سترى: Bot starting... Database ready
```

### 5) التشغيل على VPS

```bash
# على السيرفر
sudo apt update && sudo apt install python3.11 python3-pip postgresql redis -y
git clone <repo>
pip install -r requirements.txt
# إعداد .env
# systemd service
sudo nano /etc/systemd/system/earning-bot.service
```
```ini
[Unit]
Description=Telegram Earning Bot
After=network.target postgresql.service

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/Telegram Earning Platform
EnvironmentFile=/home/ubuntu/Telegram Earning Platform/.env
ExecStart=/home/ubuntu/Telegram Earning Platform/venv/bin/python main.py
Restart=always

[Install]
WantedBy=multi-user.target
```
```bash
sudo systemctl daemon-reload
sudo systemctl enable earning-bot
sudo systemctl start earning-bot
sudo systemctl status earning-bot
sudo journalctl -u earning-bot -f
```

### 6) Docker Production

```bash
cp .env.example .env
# عدّل .env (BOT_TOKEN, ADMIN_IDS, DATABASE_URL سيُحقن عبر compose)
docker-compose up -d --build
docker-compose logs -f bot
```

### 7) Render / Railway

- اربط GitHub repo
- أضف Environment Variables (BOT_TOKEN, ADMIN_IDS, DATABASE_URL, REDIS_URL)
- Build Command: `pip install -r requirements.txt`
- Start Command: `python main.py`
- لـ PostgreSQL استخدم خدمة Postgres المدمجة (Railway/Render)
- أضف `DATABASE_URL` من نوع `postgresql+asyncpg://...`
- للـ Migrations: أضف `alembic upgrade head` قبل التشغيل أو شغّل `init_db()` تلقائياً (موجود)

---

## 🔄 Backup & Restart

**Backup PostgreSQL:**
```bash
pg_dump -U earning_user -h localhost telegram_earning > backup_$(date +%F).sql
# استعادة
psql -U earning_user -h localhost telegram_earning < backup_2025-01-01.sql
# عبر Docker
docker exec <db_container> pg_dump -U earning_user telegram_earning > backup.sql
```

**Restart:**
```bash
# محلي
pkill -f main.py; python main.py &
# systemd
sudo systemctl restart earning-bot
# docker
docker-compose restart bot
```
البيانات لا تضيع لأنها في PostgreSQL (Persistence).

---

## 🔧 أوامر الإدارة داخل البوت

- `/user 123456` - عرض بيانات
- `/ban 123456` / `/unban 123456`
- `/addbalance 123456 100`
- `/set daily_reward 10` - تعديل أي إعداد
- `/createtask` - إنشاء مهمة تفاعلي
- `/deltask 5` - تعطيل مهمة
- `/createad` - إنشاء إعلان
- `/reply 5 شكراً` - رد على تذكرة دعم

الإعدادات القابلة للتعديل: `daily_reward, daily_task_points, points_to_cash, min_withdrawal_balance, min_withdrawal_amount, min_withdrawal_referrals, referral_reward, campaign_profit_percent, withdrawal_fee_percent, channel_username, support_username, maintenance_mode`...

---

## ✅ الاختبارات

```bash
pytest tests -v
# مع asyncio
pytest tests/test_bot.py -v
```

يختبر: تسجيل، إحالة، مكافأة يومية، منع تكرار، مهام، Ledger.

---

## 📈 التوسع مستقبلاً

الـ Architecture جاهز لإضافة:
- Premium (حقل is_premium + مزايا)
- Affiliate (جدول + tracking)
- Crypto Payments (Gateway)
- Web Admin Dashboard (REST API + نفس Models)
- Telegram WebApp / REST API
- Redis/Celery للمهام الخلفية
- أدوار Admin متعددة
- تعدد اللغات

يكفي إضافة Service/Model/Handler جديد دون تعديل الأساس.

---

## 📄 الترخيص

MIT - للاستخدام التجاري والتعليمي.

---

**ملاحظة:** لا تضع `BOT_TOKEN` في الكود. استخدم `.env` فقط. لا تسجل Secrets في Logs.
