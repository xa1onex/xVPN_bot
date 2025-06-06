# Токер телеграмм
import pytz
from aiogram import Router
from decouple import config
API_TOKEN = config('API_TOKEN')

# Id администраторов
ADMINS = config('ADMINS').split(',')

# ЮКасса
else:
WEBAPP_PORT = int(config("WEBAPP_PORT"))

# Формат времени
DATETIME_FORMAT = "%Y-%m-%d %H:%M"

# defining the timezone
tz = pytz.timezone('Europe/Moscow')

# Роутер
router = Router()

# Режим проограммы
mode = config('MODE')

# Настройка конфигурации ЮKassa
# Кое-т для напоминания
K_remind = 0.85

# Лимит активных подписок
ACTIVE_COUNT_SUB_LIMIT = 3

