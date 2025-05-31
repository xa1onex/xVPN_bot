import os
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import filters
from aiogram.utils import executor
from dotenv import load_dotenv
import qrcode
import io
import requests
from datetime import datetime, timedelta
import uuid
from database import Database

# Загрузка конфигурации
load_dotenv()

# Инициализация
bot = Bot(token=os.getenv('BOT_TOKEN'))
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
db = Database()


# Получение значений с обработкой отсутствия
def get_env_int(name, default):
    value = os.getenv(name)
    return int(value) if value and value.isdigit() else default


class XUI:
    """Класс для работы с 3XUI API"""

    def __init__(self):
        self.base_url = os.getenv('XUI_PANEL_URL')
        if not self.base_url:
            raise ValueError("XUI_PANEL_URL не установлен в .env")

        self.session = requests.Session()
        self.session.verify = os.getenv('XUI_SSL_VERIFY') == 'True'
        self._login()

    def _login(self):
        """Авторизация в панели"""
        login_url = f"{self.base_url}/login"
        data = {
            "username": os.getenv('XUI_USERNAME') or 'admin',
            "password": os.getenv('XUI_PASSWORD') or 'admin'
        }
        try:
            response = self.session.post(login_url, data=data)
            response.raise_for_status()
            logging.info("Успешная авторизация в 3XUI")
        except Exception as e:
            logging.error(f"Ошибка авторизации в 3XUI: {e}")
            raise

    def create_client(self, days: int = 30, limit: int = 2) -> dict:
        """Создание нового клиента"""
        client_url = f"{self.base_url}/api/inbounds/addClient"
        expiry_date = (datetime.now() + timedelta(days=days)).strftime('%Y-%m-%d')

        data = {
            "inboundId": 1,  # ID вашего инбаунда
            "enable": True,
            "email": f"{uuid.uuid4()}@vpn.bot",
            "expiryTime": expiry_date,
            "limitIp": limit,
            "totalGB": 0,  # 0 = безлимит
            "enable": True
        }

        try:
            response = self.session.post(client_url, json=data)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logging.error(f"Ошибка создания клиента: {e}")
            logging.error(f"Ответ сервера: {response.text if 'response' in locals() else ''}")
            raise

    def get_client_config(self, client_id: str) -> str:
        """Получение конфигурации клиента"""
        config_url = f"{self.base_url}/api/inbounds/getClientTraffics/{client_id}"
        try:
            response = self.session.get(config_url)
            response.raise_for_status()
            data = response.json()
            return data.get('obj', data).get('config', '')
        except Exception as e:
            logging.error(f"Ошибка получения конфигурации: {e}")
            raise


try:
    xui = XUI()
except Exception as e:
    logging.error(f"Не удалось инициализировать XUI: {e}")
    xui = None


def generate_qr(config: str) -> bytes:
    """Генерация QR-кода"""
    img = qrcode.make(config)
    byte_arr = io.BytesIO()
    img.save(byte_arr, format='PNG')
    return byte_arr.getvalue()


@dp.message_handler(commands=['start'])
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
        parse_mode="HTML"
    )


@dp.message_handler(commands=['get_vpn'])
async def get_vpn(message: types.Message):
    """Создание нового VPN подключения"""
    if not xui:
        await message.answer("⚠️ Сервис временно недоступен. Попробуйте позже.")
        return

    try:
        # Получаем значения с обработкой по умолчанию
        days = get_env_int('DEFAULT_DAYS', 30)
        limit = get_env_int('DEFAULT_DEVICE_LIMIT', 2)

        # Создаем клиента в 3XUI
        client = xui.create_client(days=days, limit=limit)

        # Получаем конфигурацию
        client_id = client.get('id') or client.get('obj', {}).get('id')
        if not client_id:
            logging.error(f"Не удалось получить ID клиента: {client}")
            raise ValueError("Неверный ответ от 3XUI API")

        config = xui.get_client_config(client_id)

        # Сохраняем в БД
        vpn_id = db.create_vpn_account(message.from_user.id, config, days)

        # Генерируем QR-код
        qr_code = generate_qr(config)

        # Отправляем пользователю
        await message.answer_photo(
            photo=qr_code,
            caption=f"<b>✅ Ваш VPN аккаунт создан!</b>\n\n"
                    f"ID: <code>{vpn_id}</code>\n"
                    f"Срок действия: {days} дней\n"
                    f"Лимит устройств: {limit}\n\n"
                    f"<b>Конфигурация:</b>\n<code>{config}</code>",
            parse_mode="HTML"
        )
    except Exception as e:
        logging.error(f"Error creating VPN: {e}")
        await message.answer("⚠️ Произошла ошибка при создании VPN. Попробуйте позже.")


@dp.message_handler(commands=['my_vpns'])
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

    await message.answer("\n".join(text), parse_mode="HTML")


@dp.message_handler(filters.RegexpCommandsFilter(regexp_commands=['/revoke_(.*)']))
async def revoke_vpn(message: types.Message, regexp_command):
    """Отзыв VPN подключения"""
    vpn_id = regexp_command.group(1)
    db.revoke_vpn_account(vpn_id)
    await message.answer(f"VPN подключение <code>{vpn_id}</code> отозвано.", parse_mode="HTML")


@dp.message_handler(commands=['help'])
async def help_command(message: types.Message):
    """Помощь"""
    await message.answer(
        "<b>Помощь по боту:</b>\n\n"
        "1. <b>/get_vpn</b> - создать новое VPN подключение\n"
        "2. <b>/my_vpns</b> - список ваших подключений\n"
        "3. <b>/revoke_ID</b> - отозвать подключение\n\n"
        "По вопросам пишите @ваш_аккаунт",
        parse_mode="HTML"
    )


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    try:
        executor.start_polling(dp, skip_updates=True)
    finally:
        db.close()