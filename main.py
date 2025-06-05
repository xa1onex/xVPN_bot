from py3xui import Api
import uuid

# Настройки
host = "http://77.110.103.180:2053/xAzd5OTnVG/"
username = "admin"
password = "admin"
external_ip = "77.110.103.180"
port = 443
remark = "gmfvbot"  # будет видно в панели

# Подключение
api = Api(host, username, password)
api.login()

# Получаем первый inbound (обычно он 1)
inbound_id = 1
inbound = api.inbound.get_by_id(inbound_id)

# Создаем нового клиента
new_uuid = str(uuid.uuid4())
email = f"user_{123456789}"  # например, Telegram ID
flow = "xtls-rprx-vision"

api.client.add(
    inbound_id=inbound_id,
    id=new_uuid,
    alter_id=0,
    email=email,
    enable=True,
    total_gb=0,  # 0 — безлимит
    expiry_time=0,  # 0 — бессрочный
    flow=flow
)

# Получаем данные из inbound, чтобы собрать ссылку
reality = inbound.stream_settings.reality_settings
public_key = reality.get("settings")["publicKey"]
short_id = reality.get("shortIds")[0]
sni = reality["serverNames"][0]

# Собираем ссылку
vless_link = (
    f"vless://{new_uuid}@{external_ip}:{port}"
    f"?type=tcp&security=reality"
    f"&pbk={public_key}&fp=chrome"
    f"&sni={sni}&sid={short_id}&spx=%2F"
    f"&flow={flow}#{remark}-{email}"
)

print("✅ Ссылка:", vless_link)