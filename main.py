import asyncio
import json
import uuid
import time
from aiogram import Bot, Dispatcher, types, F
from aiogram.enums import ParseMode
from aiogram.types import Message
from aiohttp import ClientSession

# === НАСТРОЙКИ ===
BOT_TOKEN = '7675630575:AAGgtMDc4OARX9qG7M50JWX2l3CvgbmK5EY'
XUI_API_URL = 'http://77.110.103.180:2053/xAzd5OTnVG/'
XUI_USERNAME = 'admin'
XUI_PASSWORD = 'admin'
INBOUND_ID = 1

# === Reality параметры ===
REALITY_PUBLIC_KEY = '9Hdy5jR2MNBB-vxtu1bOl4SHpiLgTWlEqgDD8ZGf2hk'
REALITY_SNI = 'yahoo.com'
REALITY_SID = 'c5b0fb2c88'
REALITY_SPX = '/'


class XUIClient:
    def __init__(self):
        self.token = None
        self.session = None

    async def login(self):
        if self.session is None:
            self.session = ClientSession()

        url = f"{XUI_API_URL}/login"
        payload = {"username": XUI_USERNAME, "password": XUI_PASSWORD}
        async with self.session.post(url, json=payload) as resp:
            data = await resp.json()
            self.token = data.get("data", {}).get("token")

    async def add_client(self, email: str):
        await self.login()
        headers = {"Authorization": self.token}
        get_url = f"{XUI_API_URL}/xui/inbound/get/{INBOUND_ID}"
        async with self.session.get(get_url, headers=headers) as r:
            inbound = (await r.json())["obj"]

        server_ip = inbound["listen"]
        if server_ip in ["0.0.0.0", "127.0.0.1", "::"]:
            server_ip = "77.110.103.180"

        new_uuid = str(uuid.uuid4())
        client_data = {
            "id": new_uuid,
            "flow": inbound['flow'],
            "email": email
        }
        inbound['settings']['clients'].append(client_data)

        update_url = f"{XUI_API_URL}/xui/inbound/update/{INBOUND_ID}"
        payload = {
            "id": INBOUND_ID,
            "up": inbound["up"],
            "down": inbound["down"],
            "total": inbound["total"],
            "remark": inbound["remark"],
            "enable": True,
            "expiryTime": 0,
            "listen": inbound["listen"],
            "port": inbound["port"],
            "protocol": inbound["protocol"],
            "settings": json.dumps(inbound["settings"]),
            "streamSettings": json.dumps(inbound["streamSettings"]),
            "sniffing": json.dumps(inbound["sniffing"])
        }
        async with self.session.post(update_url, headers=headers, json=payload) as res:
            await res.text()

        return {
            "uuid": new_uuid,
            "port": inbound["port"],
            "host": server_ip,
            "email": email
        }

    async def close(self):
        if self.session:
            await self.session.close()


bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
xui = XUIClient()


@dp.message(F.text == "/start")
async def welcome(msg: Message):
    await msg.answer("👋 Привет! Напиши /get, чтобы получить доступ к VPN.")


@dp.message(F.text == "/get")
async def get_access(msg: Message):
    email = f"user_{msg.from_user.id}_{int(time.time())}"
    try:
        user_data = await xui.add_client(email)
        vless_link = (
            f"vless://{user_data['uuid']}@{user_data['host']}:{user_data['port']}"
            f"/?type=tcp&security=reality"
            f"&pbk={REALITY_PUBLIC_KEY}"
            f"&fp=chrome&sni={REALITY_SNI}"
            f"&sid={REALITY_SID}&spx=%2F"
            f"#{user_data['email']}"
        )
        await msg.answer(f"✅ Готово! Вот твоя ссылка:\n\n`{vless_link}`", parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        await msg.answer(f"❌ Ошибка: {e}")


async def main():
    try:
        await dp.start_polling(bot)
    finally:
        await xui.close()

if __name__ == "__main__":
    asyncio.run(main())