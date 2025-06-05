from py3xui import Api
import uuid

# 📌 Настройки подключения
host = "http://77.110.103.180:2053/xAzd5OTnVG/"
username = "admin"
password = "admin"

external_ip = "77.110.103.180"
port = 443
remark = "gmfvbot"  # отображается в ссылке

# 🔐 Авторизация
api = Api(host, username, password)
api.login()

# 🔁 Получаем inbound
inbound_id = 1
inbound = api.inbound.get_by_id(inbound_id)

# 🧑‍💻 Создаем нового клиента
user_uuid = str(uuid.uuid4())
telegram_id = "user_123456"  # Подставляй ID пользователя
flow = "xtls-rprx-vision"

# ✅ Добавление клиента
api.client.add(
    inbound_id=inbound_id,
    email=telegram_id,
    enable=True,
    total_gb=0,
    expiry_time=0,
    uuid=user_uuid,
    flow=flow,
)

# 🔗 Данные из Reality
reality = inbound.stream_settings.reality_settings
public_key = reality["settings"]["publicKey"]
short_id = reality["shortIds"][0]
sni = reality["serverNames"][0]

# 🧩 Генерация VLESS-ссылки
vless_link = (
    f"vless://{user_uuid}@{external_ip}:{port}"
    f"?type=tcp&security=reality"
    f"&pbk={public_key}&fp=chrome"
    f"&sni={sni}&sid={short_id}&spx=%2F"
    f"&flow={flow}#{remark}-{telegram_id}"
)

print("✅ VLESS-ссылка:\n", vless_link)