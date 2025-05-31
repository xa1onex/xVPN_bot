import aiosqlite
import datetime

DB_PATH = "xvpn.db"

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


async def create_vpn_user(telegram_id, username=None):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT OR IGNORE INTO client (telegram_id, username, created_at)
            VALUES (?, ?, ?)
        """, (telegram_id, username, datetime.datetime.now()))
        await db.commit()

        cursor = await db.execute("SELECT * FROM client WHERE telegram_id = ?", (telegram_id,))
        return await cursor.fetchone()


async def get_user(telegram_id):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT * FROM client WHERE telegram_id = ?", (telegram_id,))
        return await cursor.fetchone()