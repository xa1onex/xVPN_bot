import sqlite3
import uuid
from datetime import datetime, timedelta


class Database:
    def __init__(self):
        self.conn = sqlite3.connect('vpn.db', check_same_thread=False)
        self._create_tables()

    def _create_tables(self):
        """Инициализация таблиц"""
        cursor = self.conn.cursor()

        # Пользователи бота
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            full_name TEXT,
            join_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')

        # VPN аккаунты
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS vpn_accounts (
            id TEXT PRIMARY KEY,
            user_id INTEGER,
            config TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP,
            is_active BOOLEAN DEFAULT TRUE,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )''')

        self.conn.commit()

    def add_user(self, user_id: int, username: str, full_name: str):
        """Добавление нового пользователя"""
        cursor = self.conn.cursor()
        cursor.execute(
            'INSERT OR IGNORE INTO users (user_id, username, full_name) VALUES (?, ?, ?)',
            (user_id, username, full_name)
        )
        self.conn.commit()

    def create_vpn_account(self, user_id: int, config: str, days: int) -> str:
        """Создание VPN аккаунта"""
        vpn_id = str(uuid.uuid4())
        expires_at = datetime.now() + timedelta(days=days)

        cursor = self.conn.cursor()
        cursor.execute(
            'INSERT INTO vpn_accounts (id, user_id, config, expires_at) VALUES (?, ?, ?, ?)',
            (vpn_id, user_id, config, expires_at)
        )
        self.conn.commit()
        return vpn_id

    def get_user_accounts(self, user_id: int) -> list:
        """Получение всех аккаунтов пользователя"""
        cursor = self.conn.cursor()
        cursor.execute(
            'SELECT id, config, expires_at, is_active FROM vpn_accounts WHERE user_id = ?',
            (user_id,)
        )
        return cursor.fetchall()

    def revoke_vpn_account(self, vpn_id: str):
        """Отзыв VPN аккаунта"""
        cursor = self.conn.cursor()
        cursor.execute(
            'UPDATE vpn_accounts SET is_active = FALSE WHERE id = ?',
            (vpn_id,)
        )
        self.conn.commit()

    def close(self):
        """Закрытие соединения"""
        self.conn.close()