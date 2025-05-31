import os
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import FSInputFile
from aiogram.enums import ParseMode
from dotenv import load_dotenv
import qrcode
import io
import requests
from datetime import datetime, timedelta
from database import Database

# Загрузка конфигурации
load_dotenv()

# Инициализация
bot = Bot(token=os.getenv('BOT_TOKEN'))
dp = Dispatcher()
db = Database()


class XUI:
    """Класс для работы с 3XUI API"""

    def __init__(self):
        self.base_url = os.getenv('XUI_PANEL_URL')
        self.session = requests.Session()
        self.session.verify = os.getenv('XUI_SSL_VERIFY') == 'True'
        self._login()

    def _login(self):
        """Авторизация в панели"""
        login_url = f"{self.base_url}/login"
        data = {
            "username": os.getenv('XUI_USERNAME'),
            "password": os.getenv('XUI_PASSWORD')
        }
        response = self.session.post(login_url, data=data)
        response.raise_for_status()

    def create_client(self, days: int = 30, limit: int = 2) -> dict:
        """Создание нового клиента"""
        client_url = f"{self.base_url}/api/inbounds/addClient"
        expiry_date = (datetime.now() + timedelta(days=days)).strftime('%Y-%m-%d')

        data = {
            "inboundId": 1,  # ID вашего инбаунда
            "enable": True,
            "email": str(uuid.uuid4()),
            "expiryTime": expiry_date,
            "limitIp": limit,
            "totalGB": 0,  # 0 = безлимит
            "enable": True
        }

        response = self.session.post(client_url, json=data)
        response.raise_for_status()
        return response.json()

    def get_client_config(self, client_id: str) -> str:
        """Получение конфигурации клиента"""
        config_url = f"{self.base_url}/api/inbounds/getClientTraffics/{client_id}"
        response = self.session.get(config_url)
        response.raise_for_status()
        return response.json().get('config', '')


xui = XUI()


def generate_qr(config: str) -> io.BytesIO:
    """Генерация QR-кода"""
    img = qrcode.make(config)
    byte_arr = io.BytesIO()
    img.save(byte_arr, format='PNG')
    byte_arr.seek(0)
    return byte_arr


@dp.message(Command('start'))
async def start(message: types.Message):
    """Обработчик команды /start"""
    user = message.from_user
    db.add_user(user.id, user.username, user.full_name)

    await message.answer(
        "🔐 <b>VPN Bot</b>\n\n"
        "Доступные команды:\n"
        "/get_vpn - Получить VPN конфиг\n"
        "/my_vpns - Мои подключения\n"
        "/help - Помощь",
        parse_mode=ParseMode.HTML
    )


@dp.message(Command('get_vpn'))
async def get_vpn(message: types.Message):
    """Создание нового VPN подключения"""
    try:
        # Создаем клиента в 3XUI
        client = xui.create_client(
            days=int(os.getenv('DEFAULT_DAYS')),
            limit=int(os.getenv('DEFAULT_DEVICE_LIMIT'))

        # Получаем конфигурацию
        config = xui.get_client_config(client['id'])

        # Сохраняем в БД
        vpn_id = db.create_vpn_account(message.from_user.id, config, int(os.getenv('DEFAULT_DAYS')))

        # Генерируем QR-код
        qr_code = generate_qr(config)

        # Отправляем пользователю
        await message.answer_photo(
            photo=types.BufferedInputFile(qr_code.read(), filename='vpn_qr.png'),
            caption=f"<b>✅ Ваш VPN аккаунт создан!</b>\n\n"
                    f"ID: <code>{vpn_id}</code>\n"
                    f"Срок действия: {os.getenv('DEFAULT_DAYS')} дней\n\n"
                    f"<b>Конфигурация:</b>\n<code>{config}</code>",
            parse_mode=ParseMode.HTML
        )
    except Exception as e:
        logging.error(f"Error creating VPN: {e}")
        await message.answer("⚠️ Произошла ошибка при создании VPN. Попробуйте позже.")


@dp.message(Command('my_vpns'))
async def list_vpns(message: types.Message):
    """Список всех VPN пользователя"""
    accounts = db.get_user_accounts(message.from_user.id)

    if not accounts:
        await message.answer("У вас нет активных VPN подключений.")
        return

    text = ["<b>Ваши VPN подключения:</b>\n"]
    for acc in accounts:
        status = "🟢 Активен" if acc[3] else "🔴 Неактивен"
        text.append(
            f"\nID: <code>{acc[0]}</code>\n"
            f"Статус: {status}\n"
            f"Истекает: {acc[2]}\n"
            f"/revoke_{acc[0]} - Отозвать"
        )

    await message.answer("\n".join(text), parse_mode=ParseMode.HTML)


@dp.message(lambda message: message.text.startswith('/revoke_'))
async def revoke_vpn(message: types.Message):
    """Отзыв VPN подключения"""
    vpn_id = message.text.replace('/revoke_', '')
    db.revoke_vpn_account(vpn_id)
    await message.answer(f"VPN подключение <code>{vpn_id}</code> отозвано.", parse_mode=ParseMode.HTML)


@dp.message(Command('help'))
async def help_command(message: types.Message):
    """Помощь"""
    await message.answer(
        "<b>Помощь по боту:</b>\n\n"
        "1. <b>/get_vpn</b> - создать новое VPN подключение\n"
        "2. <b>/my_vpns</b> - список ваших подключений\n"
        "3. <b>/revoke_ID</b> - отозвать подключение\n\n"
        "По вопросам пишите @ваш_аккаунт",
        parse_mode=ParseMode.HTML
    )


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    try:
        dp.run_polling(bot)
    finally:
        db.close()