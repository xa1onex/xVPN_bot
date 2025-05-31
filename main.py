import os
import json
import uuid
import requests
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.enums import ParseMode
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
PANEL_HOST = os.getenv("PANEL_HOST")
REALITY_FALLBACK_SNI = os.getenv("SNI", "google.com")

bot = Bot(BOT_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()
session = requests.Session()


def get_client_link(username: str) -> str | None:
    try:
        response = session.get(f"{PANEL_HOST}/panel/api/inbounds/list")
        response.raise_for_status()
        data = response.json()

        for inbound in data.get("obj", []):
            if inbound.get("protocol") != "vless":
                continue

            settings = json.loads(inbound.get("settings", "{}"))
            clients = settings.get("clients", [])

            for client in clients:
                if client.get("email") == username:
                    client_id = client["id"]

                    stream_settings = json.loads(inbound.get("streamSettings", "{}"))
                    reality = stream_settings.get("realitySettings", {})

                    pbk = reality.get("settings", {}).get("publicKey")
                    if not pbk:
                        return None

                    address = inbound.get("listen") or inbound.get("address")
                    port = inbound.get("port")
                    sni = reality.get("serverNames", [REALITY_FALLBACK_SNI])[0]
                    sid = reality.get("shortIds", ["random"])[0]

                    return (
                        f"vless://{client_id}@{address}:{port}/"
                        f"?type=tcp&security=reality&pbk={pbk}&fp=chrome"
                        f"&sni={sni}&sid={sid}&spx=%2F&flow=xtls-rprx-vision"
                        f"#vpn-{username}"
                    )
        return None
    except Exception as e:
        print("❌ Ошибка при получении ссылки:", e)
        return None


@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("Привет! Отправь команду /get чтобы получить свою VPN-ссылку.")


@dp.message(Command("get"))
async def cmd_get(message: types.Message):
    user_id = message.from_user.id
    username = f"user_{user_id}"

    link = get_client_link(username)

    if link:
        await message.answer(f"🔗 Ваша ссылка:\n<code>{link}</code>")
    else:
        await message.answer("❌ Клиент не найден в панели 3x-ui.\nВозможно, его нужно сначала добавить вручную или через бота.")


if __name__ == "__main__":
    import asyncio
    from aiogram import executor
    executor.start_polling(dp, skip_updates=True)