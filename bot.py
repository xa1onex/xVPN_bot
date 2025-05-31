from aiogram import Bot, Dispatcher, types
from aiogram.types import Message
from aiogram.utils import executor
from db import create_vpn_user
import config
import db

bot = Bot(token=config.BOT_TOKEN)
dp = Dispatcher(bot)

@dp.message_handler(commands=["start"])
async def cmd_start(message: Message):
    await message.answer("Привет! Я выдам тебе VPN-доступ. Напиши /get")

@dp.message_handler(commands=['get'])
async def cmd_get(message: types.Message):
    email = await create_vpn_user(message.from_user.id)

    domain = "xdouble.duckdns.org"
    uuid_str = email.split('-')[1].split('@')[0]  # генерация UUID по шаблону
    vpn_link = f"vless://{uuid_str}@{domain}:443?encryption=none&security=tls&type=ws#xVPN"

    await message.reply(f"✅ Вот ваш VPN-доступ на 3 дня:\n\n{vpn_link}")

async def on_startup(dp):
    await db.init_db()

if __name__ == "__main__":
    executor.start_polling(dp, on_startup=on_startup)