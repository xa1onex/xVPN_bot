from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from telebot.types import Message
from database.models import User, Server
from config_data.config import DEFAULT_COMMANDS, ADMIN_COMMANDS, ALLOWED_USERS
from loader import bot


@bot.message_handler(commands=['help'])
def bot_help(message: Message):
    commands = [f"/{command} - {description}" for command, description in DEFAULT_COMMANDS]
    if message.from_user.id in ALLOWED_USERS:
        commands.extend([f"/{command} - {description}" for command, description in ADMIN_COMMANDS])
    bot.reply_to(message, "📋 Доступные команды:\n" + "\n".join(commands))
    bot.send_message(message.chat.id, "🤝 Для поддержки обращайтесь: @guardtunnel_support")

@bot.message_handler(commands=['servers'])  # Используем команду /servers
async def send_servers_markup(message: Message):
    markup = get_servers_markup()
    await message.answer("Выберите сервер:", reply_markup=markup)

def get_servers_markup():
    """ Inline buttons для выдачи всех локаций серверов """
    actions = InlineKeyboardMarkup(row_width=1)
    servers_obj = Server.select()
    for server in servers_obj:
        actions.add(InlineKeyboardButton(text=f"🌍 {server.location}", callback_data=str(server.id)))
    actions.add(InlineKeyboardButton(text=f"➕ Добавить сервер", callback_data="Add"))
    return actions