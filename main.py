import os
import json
import uuid
import sqlite3
import time
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message
from aiogram.utils import executor
from dotenv import load_dotenv

# Загрузка переменных из .env
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
SERVER_IP = os.getenv("SERVER_IP")
SERVER_PORT = os.getenv("SERVER_PORT", "443")
PBK = os.getenv("PBK")
SNI = os.getenv("SNI")
DB_PATH = "/etc/x-ui/x-ui.db"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

def generate_vless_link(email: str, uuid_: str) -> str:
    return f"vless://{uuid_}@{SERVER_IP}:{SERVER_PORT}/?type=tcp&security=reality&pbk={PBK}&fp=chrome&sni={SNI}&sid={uuid.uuid4().hex[:16]}&spx=%2F#{email}"

@dp.message_handler(commands=["start"])
async def start(msg: Message):
    await msg.answer("Привет! Напиши /get, чтобы получить VPN-ссылку.")

@dp.message_handler(commands=["get"])
async def get_vpn(msg: Message):
    user_id = msg.from_user.id
    username = msg.from_user.username or f"user{user_id}"
    email = f"{username}_{user_id}_{int(time.time())}"
    uuid_str = str(uuid.uuid4())

    # Подключение к SQLite
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT settings FROM inbounds WHERE protocol = 'vless'")
    result = cursor.fetchone()
    if not result:
        await msg.answer("❌ VLESS inbound не найден.")
        conn.close()
        return

    settings_json = json.loads(result[0])
    clients = settings_json.get("clients", [])

    # Проверка на дубликаты
    if any(client.get("email") == email for client in clients):
        await msg.answer("❗ Такой пользователь уже существует.")
        conn.close()
        return

    new_client = {
        "id": uuid_str,
        "email": email,
        "flow": "xtls-rprx-vision"
    }

    clients.append(new_client)
    settings_json["clients"] = clients

    new_settings_str = json.dumps(settings_json)

    # Обновление базы
    cursor.execute("UPDATE inbounds SET settings = ? WHERE protocol = 'vless'", (new_settings_str,))
    conn.commit()
    conn.close()

    link = generate_vless_link(email, uuid_str)
    await msg.answer(f"✅ Готово! Вот твоя ссылка:\n\n<code>{link}</code>", parse_mode="HTML")

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)