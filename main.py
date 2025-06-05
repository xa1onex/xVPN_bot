from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import requests
import uuid

# === Настройки ===
BOT_TOKEN = '7675630575:AAGgtMDc4OARX9qG7M50JWX2l3CvgbmK5EY'
PANEL_URL = 'http://77.110.103.180:2053/xAzd5OTnVG'
USERNAME = 'admin'
PASSWORD = 'admin'

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Напиши /getvpn — выдам VLESS конфиг на твой ник.")

async def getvpn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user.username or "anon"
    client_id = str(uuid.uuid4())

    # Авторизация
    login = requests.post(f"{PANEL_URL}/login", json={
        "username": USERNAME,
        "password": PASSWORD
    })
    if not login.ok:
        await update.message.reply_text("❌ Не удалось войти в панель.")
        return
    token = login.json()["data"]["token"]
    headers = {"Authorization": token}

    # Добавление пользователя
    user_data = {
        "enable": True,
        "remark": f"tg_{user}",
        "expiryTime": 0,
        "listen": "",
        "port": 0,
        "protocol": "vless",
        "settings": {
            "clients": [
                {"id": client_id, "flow": "", "email": f"{user}@tg"}
            ]
        },
        "streamSettings": {
            "network": "tcp"
        },
        "sniffing": {
            "enabled": True,
            "destOverride": ["http", "tls"]
        }
    }

    res = requests.post(f"{PANEL_URL}/panel/inbound/add", json=user_data, headers=headers)
    if not res.ok or not res.json().get("success"):
        await update.message.reply_text("⚠️ Ошибка при создании пользователя.")
        return

    inbound = res.json()["data"]
    port = inbound.get("port")
    address = "77.110.103.180"

    vless_link = f"vless://{client_id}@{address}:{port}?encryption=none&type=tcp#{user}"

    await update.message.reply_text(f"✅ Готово! Вот твой VLESS конфиг:\n\n`{vless_link}`", parse_mode="Markdown")

app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("getvpn", getvpn))

app.run_polling()