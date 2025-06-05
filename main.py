import asyncio
import json
import uuid
from aiohttp import ClientSession, CookieJar
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

API_BASE = "http://77.110.103.180:2053/xAzd5OTnVG"
USERNAME = "admin"
PASSWORD = "admin"
VLESS_HOST = "77.110.103.180"
VLESS_PORT = 443
PBK = "9Hdy5jR2MNBB-vxtu1bOl4SHpiLgTWlEqgDD8ZGf2hk"
SNI = "yahoo.com"

BOT_TOKEN = "7675630575:AAGgtMDc4OARX9qG7M50JWX2l3CvgbmK5EY"

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

async def login(session: ClientSession):
    url = f"{API_BASE}/login"
    payload = {"username": USERNAME, "password": PASSWORD}
    async with session.post(url, json=payload) as resp:
        data = await resp.json()
        if not data["success"]:
            raise Exception("Login failed")

async def add_user(session: ClientSession, email: str):
    await login(session)
    user_id = str(uuid.uuid4())
    payload = {
        "id": None,
        "up": 0,
        "down": 0,
        "total": 0,
        "remark": email,
        "enable": True,
        "expiryTime": 0,
        "listen": "",
        "port": VLESS_PORT,
        "protocol": "vless",
        "settings": json.dumps({
            "clients": [
                {
                    "id": user_id,
                    "email": email
                }
            ],
            "decryption": "none",
            "fallbacks": []
        }),
        "streamSettings": json.dumps({
            "network": "tcp",
            "security": "reality",
            "realitySettings": {
                "show": False,
                "fingerprint": "chrome",
                "serverName": SNI,
                "publicKey": PBK,
                "shortId": "",
                "spiderX": "/"
            }
        }),
        "sniffing": json.dumps({
            "enabled": True,
            "destOverride": ["http", "tls"]
        })
    }

    url = f"{API_BASE}/inbound/add"
    async with session.post(url, json=payload) as resp:
        result = await resp.json()
        if result["success"]:
            return f"vless://{user_id}@{VLESS_HOST}:{VLESS_PORT}/?type=tcp&security=reality&pbk={PBK}&fp=chrome&sni={SNI}&sid=&spx=%2F#{email}"
        else:
            raise Exception("Failed to add user")

async def main():
    session = ClientSession(cookie_jar=CookieJar())

    @dp.message(F.text == "/get")
    async def get_vpn(message: Message):
        try:
            email = f"tg_{message.from_user.id}"
            link = await add_user(session, email)
            await message.answer(f"✅ Вот твоя ссылка:\n<code>{link}</code>")
        except Exception as e:
            await message.answer(f"❌ Ошибка: {e}")

    try:
        await dp.start_polling(bot)
    finally:
        await session.close()

if __name__ == "__main__":
    asyncio.run(main())