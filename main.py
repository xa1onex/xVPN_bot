import asyncio
import uuid
from aiohttp import ClientSession
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage

# ==== CONFIG ====
BOT_TOKEN = "7675630575:AAGgtMDc4OARX9qG7M50JWX2l3CvgbmK5EY"
XUI_API_URL = "http://77.110.103.180:2053/xAzd5OTnVG"
XUI_USERNAME = "admin"
XUI_PASSWORD = "admin"
VLESS_DOMAIN = "77.110.103.180"
VLESS_PORT = 443
VLESS_PBK = "9Hdy5jR2MNBB-vxtu1bOl4SHpiLgTWlEqgDD8ZGf2hk"
VLESS_SNI = "yahoo.com"
# ================

class XUIClient:
    def __init__(self, api_url, username, password):
        self.api_url = api_url
        self.username = username
        self.password = password
        self.session = ClientSession()

    async def login(self):
        url = f"{self.api_url}/login"
        payload = {"username": self.username, "password": self.password}
        async with self.session.post(url, json=payload) as resp:
            if resp.content_type != "application/json":
                text = await resp.text()
                raise Exception(f"API не вернул JSON: {text}")
            data = await resp.json()
            if not data.get("success"):
                raise Exception(f"Логин не удался: {data.get('msg')}")

    async def add_user(self, email):
        await self.login()
        # uuid + subId
        user_id = str(uuid.uuid4())
        sub_id = uuid.uuid4().hex[:16]

        payload = {
            "up": 0,
            "down": 0,
            "total": 0,
            "remark": email,
            "enable": True,
            "expiryTime": 0,
            "listen": "",
            "port": VLESS_PORT,
            "protocol": "vless",
            "settings": {
                "clients": [{
                    "id": user_id,
                    "email": email,
                    "flow": "xtls-rprx-vision",
                    "enable": True,
                    "limitIp": 0,
                    "totalGB": 0,
                    "expiryTime": 0,
                    "subId": sub_id
                }]
            },
            "streamSettings": {
                "network": "tcp",
                "security": "reality",
                "realitySettings": {
                    "show": False,
                    "fingerprint": "chrome",
                    "serverName": VLESS_SNI,
                    "publicKey": VLESS_PBK,
                    "shortId": sub_id,
                    "spiderX": "/"
                }
            },
            "sniffing": {
                "enabled": True,
                "destOverride": ["http", "tls"]
            }
        }

        url = f"{self.api_url}/panel/inbound/add"
        async with self.session.post(url, json=payload) as resp:
            result = await resp.json()
            if result.get("success"):
                return {
                    "uuid": user_id,
                    "email": email,
                    "sub_id": sub_id
                }
            else:
                raise Exception(f"Ошибка при добавлении: {result.get('msg')}")

    async def close(self):
        await self.session.close()


bot = Bot(token=BOT_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher(storage=MemoryStorage())
xui = XUIClient(XUI_API_URL, XUI_USERNAME, XUI_PASSWORD)


@dp.message(Command("start"))
async def start(msg: Message):
    await msg.answer("Привет! Напиши /get чтобы получить доступ к VPN.")

@dp.message(Command("get"))
async def get_vpn(msg: Message):
    email = f"user_{msg.from_user.id}"
    try:
        data = await xui.add_user(email)
        link = (
            f"vless://{data['uuid']}@{VLESS_DOMAIN}:{VLESS_PORT}"
            f"?type=tcp&security=reality&pbk={VLESS_PBK}&fp=chrome"
            f"&sni={VLESS_SNI}&sid={data['sub_id']}&spx=%2F#{email}"
        )
        await msg.answer(f"🔗 Вот твоя VLESS-ссылка:\n<code>{link}</code>")
    except Exception as e:
        await msg.answer(f"❌ Ошибка: {str(e)}")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())