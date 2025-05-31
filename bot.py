from aiogram import Bot, Dispatcher, types
from aiogram.types import Message
from aiogram.utils import executor
import config
import db

bot = Bot(token=config.BOT_TOKEN)
dp = Dispatcher(bot)

@dp.message_handler(commands=["start"])
async def cmd_start(message: Message):
    await message.answer("Привет! Я выдам тебе VPN-доступ. Напиши /get")

@dp.message_handler(commands=["get"])
async def cmd_get(message: Message):
    result = await db.create_vpn_user(message.from_user.id)
    await message.answer(result)

async def on_startup(dp):
    await db.init_db()

if __name__ == "__main__":
    executor.start_polling(dp, on_startup=on_startup)