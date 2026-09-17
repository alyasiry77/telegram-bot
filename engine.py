from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base
from config import settings

engine = create_async_engine(
    settings.database_url,
    echo=False,
    future=True
)

async_session = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

Base = declarative_base()

async def init_db():
    async with engine.begin() as conn:
        # يمكنك تفعيل السطر التالي إذا أردت إنشاء الجداول تلقائياً عند بدء التشغيل
        # await conn.run_sync(Base.metadata.create_all)
        pass
