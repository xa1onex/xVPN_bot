from py3xui import Api
from py3xui.schemas import Client
import uuid

# Настройки
host = "http://77.110.103.180:2053/xAzd5OTnVG/"
username = "admin"
password = "admin"
external_ip = "77.110.103.180"
port = 443
remark = "gmfvbot"

# Подключение
api = Api(host, username, password)
api.login()

# Получаем inbound
inbound_id = 1
inbound = api.inbound.get_by_id(inbound_id)

# Создаем клиента
new_uuid = str(uuid.uuid4())
email = f"user_{123456789}"  # Telegram ID
flow = "xtls-rprx-vision"

client = Client(
    email=email,
    enable=True,
    total_gb=0,  # Безлимит
    expiry_time=0,  # Бессрочно
    flow=flow
    # ❗ uuid НЕ передается — он будет сгенерирован автоматически
)

# Добавляем клиента
api.client.add(inbound_id, client)

# Парсим Reality-параметры
reality = inbound.stream_settings.reality_settings
public_key = reality.get("settings")["publicKey"]
short_id = reality.get("shortIds")[0]
sni = reality["serverNames"][0]

# Собираем ссылку
vless_link = (
    f"vless://{client.id}@{external_ip}:{port}"
    f"?type=tcp&security=reality"
    f"&pbk={public_key}&fp=chrome"
    f"&sni={sni}&sid={short_id}&spx=%2F"
    f"&flow={flow}#{remark}-{email}"
)

print("✅ Ссылка:", vless_link)