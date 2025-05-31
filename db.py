import aiosqlite
from datetime import datetime, timedelta
import uuid

DB_PATH = "/etc/x-ui/x-ui.db"

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS client (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER UNIQUE NOT NULL,
                username TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.commit()


async def create_vpn_user(telegram_id):
    async with aiosqlite.connect(DB_PATH) as db:
        now = datetime.utcnow()
        expire = now + timedelta(days=3)
        email = f"{telegram_id}-{uuid.uuid4().hex[:6]}@xvpn"

        # VLESS пример с фейковыми настройками
        await db.execute("""
            INSERT INTO client (
                enable, email, uuid, flow, total, expiry_time, listen_port, protocol, sub_id, up, down
            ) VALUES (
                1, ?, ?, '', 0, ?, 443, 'vless', '', 0, 0
            );
        """, (email, str(uuid.uuid4()), int(expire.timestamp())))
        await db.commit()
        return email

async def get_user(telegram_id):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT * FROM client WHERE telegram_id = ?", (telegram_id,))
        return await cursor.fetchone()