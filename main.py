import asyncio
import uuid
import sqlite3
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.enums import ParseMode

# 🛠 Настройки
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


def add_user_to_inbound(uuid_str: str, email: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Найдём первый inbound с VLESS
    cursor.execute("SELECT id, settings FROM inbounds WHERE protocol = 'vless' LIMIT 1")
    row = cursor.fetchone()
    if not row:
        conn.close()
        raise Exception("VLESS inbound не найден")

    inbound_id, settings_json = row
    settings = json.loads(settings_json)

    # Добавим клиента в JSON
    new_client = {
        "id": uuid_str,
        "email": email,
        "flow": FLOW
    }

    if "clients" not in settings:
        settings["clients"] = []

    settings["clients"].append(new_client)

    # Обновим запись
    new_settings_json = json.dumps(settings)
    cursor.execute("UPDATE inbounds SET settings = ? WHERE id = ?", (new_settings_json, inbound_id))
    conn.commit()
    conn.close()


@dp.message(Command("get"))
async def handle_get(message: types.Message):
    try:
        user_id = message.from_user.id
        username = message.from_user.username or f"user{user_id}"
        user_uuid = generate_uuid()
        email = f"{username}_{user_id}"

        add_user_to_inbound(user_uuid, email)

        vless_link = get_vless_link(user_uuid, SERVER_IP, PORT, FLOW, TLS, email)
        await message.answer(f"🎉 Ваш VLESS VPN доступ:\n\n<code>{vless_link}</code>", parse_mode=ParseMode.HTML)

    except Exception as e:
        await message.answer(f"⚠️ Ошибка: {e}")


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())