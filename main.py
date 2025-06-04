import asyncio
import json
import uuid
import time
from aiogram import Bot, Dispatcher, types
from aiohttp import ClientSession

# === НАСТРОЙКИ ===
BOT_TOKEN = '7675630575:AAGgtMDc4OARX9qG7M50JWX2l3CvgbmK5EY'
XUI_API_URL = 'http://77.110.103.180:2053/xAzd5OTnVG/'
XUI_USERNAME = 'admin'
XUI_PASSWORD = 'admin'
INBOUND_ID = 1  # ID VLESS-инбунда в x-ui


# === Авторизация и создание сессии ===
class XUIClient:
    def __init__(self):
        self.token = None
        self.session = ClientSession()

    async def login(self):
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
            "host": inbound["listen"],
            "email": email
        }

    async def close(self):
        await self.session.close()


# === Бот ===
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

xui = XUIClient()


@dp.message(commands=["start", "help"])
async def welcome(msg: types.Message):
    await msg.answer("Привет! Напиши /get чтобы получить VPN-доступ.")


@dp.message(commands=["get"])
async def get_access(msg: types.Message):
    email = f"user_{msg.from_user.id}_{int(time.time())}"
    try:
        user_data = await xui.add_client(email)
        vless_link = (
            f"vless://{user_data['uuid']}@{user_data['host']}:{user_data['port']}"
            f"/?type=tcp&security=reality"
            f"&pbk=9Hdy5jR2MNBB-vxtu1bOl4SHpiLgTWlEqgDD8ZGf2hk"
            f"&fp=chrome&sni=yahoo.com"
            f"&sid=c5b0fb2c88&spx=%2F"
            f"#{user_data['email']}"
        )
        await msg.answer(f"Вот твоя ссылка:\n\n`{vless_link}`", parse_mode="Markdown")
    except Exception as e:
        await msg.answer(f"Ошибка: {e}")


async def main():
    try:
        await dp.start_polling(bot)
    finally:
        await xui.close()


if __name__ == "__main__":
    asyncio.run(main())