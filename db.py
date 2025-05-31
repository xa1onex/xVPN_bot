import aiosqlite
import config
import uuid
from datetime import datetime, timedelta

DB_PATH = "xvpn.db"

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS client (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER UNIQUE,
                username TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.commit()

async def create_vpn_user(tg_user_id):
    user_id = str(uuid.uuid4())
    expire_days = 3
    expire = int((datetime.now() + timedelta(days=expire_days)).timestamp())

    inbound_id = 1  # если у тебя 1 правило — можно зафиксировать

    async with aiosqlite.connect(config.XUI_DB_PATH) as db:
        await db.execute(
            "INSERT INTO client (id, remark, enable, email, expiryTime, total, up, down, tgId, subId, inboundId) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                user_id,
                f"telegram_{tg_user_id}",
                1,
                f"{tg_user_id}@vpn",
                expire,
                0,
                0,
                0,
                str(tg_user_id),
                str(uuid.uuid4()),
                inbound_id
            )
        )
        await db.commit()

    return f"✅ Пользователь создан!\nID: {user_id}\nСрок: {expire_days} дня"