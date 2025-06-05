import uuid
import httpx
import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.enums import ParseMode
from aiogram.filters import Command
from dotenv import load_dotenv
import os

load_dotenv()

bot = Bot(token=os.getenv("BOT_TOKEN"))
dp = Dispatcher()

XUI_URL = os.getenv("XUI_BASE_URL")
XUI_USER = os.getenv("XUI_USERNAME")
XUI_PASS = os.getenv("XUI_PASSWORD")

HEADERS = {"Content-Type": "application/json"}


async def xui_login() -> dict:
    async with httpx.AsyncClient(base_url=XUI_URL, follow_redirects=True) as temp_client:
        resp = await temp_client.post("/login", data={"username": XUI_USER, "password": XUI_PASS})
        if resp.status_code != 200 or "Set-Cookie" not in resp.headers:
            raise Exception("Не удалось авторизоваться в 3x-ui")
        cookies = temp_client.cookies
        return cookies

async def create_vless_user(telegram_id: int):
    cookies = await xui_login()
    async with httpx.AsyncClient(base_url=XUI_URL, cookies=cookies) as client:
        user_uuid = str(uuid.uuid4())
        user_tag = f"user_{telegram_id}"
        short_id = uuid.uuid4().hex[:8]

        data = {
            "enable": True,
            "remark": user_tag,
            "listen": "",
            "port": 443,
            "protocol": "vless",
            "settings": {
                "clients": [
                    {
                        "id": user_uuid,
                        "flow": "xtls-rprx-vision",
                        "email": user_tag
                    }
                ],
                "decryption": "none",
                "fallbacks": []
            },
            "streamSettings": {
                "network": "tcp",
                "security": "reality",
                "realitySettings": {
                    "show": False,
                    "dest": "yahoo.com:443",
                    "xver": 0,
                    "serverNames": ["yahoo.com"],
                    "fingerprint": "chrome",
                    "publicKey": "9Hdy5jR2MNBB-vxtu1bOl4SHpiLgTWlEqgDD8ZGf2hk",
                    "shortId": short_id,
                    "spiderX": "/"
                }
            },
            "sniffing": {
                "enabled": True,
                "destOverride": ["http", "tls"]
            }
        }

        resp = await client.post("/xui/inbound/add", json=data)
        if resp.status_code != 200:
            raise Exception(f"Ошибка при создании пользователя: {resp.text}")

        link = (
            f"vless://{user_uuid}@77.110.103.180:443/?type=tcp"
            f"&security=reality"
            f"&pbk=9Hdy5jR2MNBB-vxtu1bOl4SHpiLgTWlEqgDD8ZGf2hk"
            f"&fp=chrome"
            f"&sni=yahoo.com"
            f"&sid={short_id}"
            f"&spx=%2F"
            f"&flow=xtls-rprx-vision"
            f"#{user_tag}"
        )

        return link


@dp.message(Command("get"))
async def handle_get(message: Message):
    await message.answer("⏳ Генерирую ссылку, подожди секунду...")
    try:
        link = await create_vless_user(message.from_user.id)
        await message.answer(f"✅ Готово! Вот твоя ссылка:\n<code>{link}</code>", parse_mode=ParseMode.HTML)
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")


async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())