import asyncio
import uuid
import sqlite3
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.enums import ParseMode

API_TOKEN = "7675630575:AAGgtMDc4OARX9qG7M50JWX2l3CvgbmK5EY"
DB_PATH = "/etc/x-ui/x-ui.db"  # путь к базе данных 3x-ui
SERVER_IP = "77.110.103.180"
PORT = 443  # Порт VLESS
FLOW = "xtls-rprx-vision"
TLS = "tls"

bot = Bot(token=API_TOKEN)
dp = Dispatcher()


def generate_uuid():
    return str(uuid.uuid4())


def get_vless_link(user_uuid, server_ip, port, flow, tls, name):
    return f"vless://{user_uuid}@{server_ip}:{port}?type=ws&security={tls}&encryption=none&flow={flow}#{name}"


def add_user_to_db(uuid_str: str, email: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Найдём первый доступный inbound с VLESS
    cursor.execute("SELECT id FROM inbounds WHERE protocol = 'vless' LIMIT 1")
    row = cursor.fetchone()
    if not row:
        conn.close()
        raise Exception("VLESS inbound не найден")
    inbound_id = row[0]

    # Добавим клиента
    cursor.execute(
        "INSERT INTO clients (id, inbound_id, email, uuid, alterId, enable, expiryTime, tgId) VALUES (NULL, ?, ?, ?, 0, 1, 0, '')",
        (inbound_id, email, uuid_str)
    )

    conn.commit()
    conn.close()


@dp.message(Command("get"))
async def handle_get(message: types.Message):
    try:
        user_id = message.from_user.id
        user_uuid = generate_uuid()
        email = f"user_{user_id}"

        add_user_to_db(user_uuid, email)

        vless_link = get_vless_link(user_uuid, SERVER_IP, PORT, FLOW, TLS, email)
        await message.answer(f"🎉 Ваш VLESS VPN доступ:\n\n<code>{vless_link}</code>", parse_mode=ParseMode.HTML)

    except Exception as e:
        await message.answer(f"⚠️ Ошибка: {e}")


async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())