import telebot
import ssl
import socket
from OpenSSL import crypto
from urllib.parse import urlparse
from datetime import datetime
from zoneinfo import ZoneInfo
import logging
from logging.handlers import TimedRotatingFileHandler
import re
import sys

# ------------------- ЛОГИРОВАНИЕ -------------------
class ZoneFormatter(logging.Formatter):
    def __init__(self, fmt=None, datefmt=None, tz="Asia/Yekaterinburg"):
        super().__init__(fmt=fmt, datefmt=datefmt)
        self.tz = ZoneInfo(tz)

    def formatTime(self, record, datefmt=None):
        dt = datetime.fromtimestamp(record.created, tz=self.tz)
        if datefmt:
            return dt.strftime(datefmt)
        return dt.strftime("%Y-%m-%d %H:%M:%S")

logger = logging.getLogger("postman_bot")
logger.setLevel(logging.INFO)

# Определяем, где мы запущены (тесты или продакшн)
import sys
if 'pytest' in sys.modules:
    # Запуск в тестах - используем временную папку
    log_dir = os.path.join(os.path.dirname(__file__), 'logs')
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, 'bot.log')
else:
    # Запуск на сервере
    log_file = "/home/ioxnsun/SSL-BOT-for-telegram/bot.log"
    # Создаем папку для логов на сервере (если её нет)
    os.makedirs(os.path.dirname(log_file), exist_ok=True)

if not logger.handlers:
    file_handler = TimedRotatingFileHandler(
        log_file,
        when="D",
        interval=1,
        backupCount=7
    )
    formatter = ZoneFormatter("%(asctime)s [%(levelname)s] %(message)s",
                              datefmt="%Y-%m-%d %H:%M:%S",
                              tz="Asia/Yekaterinburg")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Добавляем вывод в консоль
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

# ------------------- TELEGRAM BOT -------------------
TOKEN = "{{token}}"
bot = telebot.TeleBot(TOKEN)

user_states = {}

# ------------------- HELPERS -------------------
def user_info(message_or_call):
    if hasattr(message_or_call, "from_user"):
        user = message_or_call.from_user
    else:
        user = message_or_call.message.from_user
    return f"id={user.id}, username={user.username}, name={user.first_name} {user.last_name or ''}".strip()

def escape_markdown(text: str) -> str:
    escape_chars = r'_*[]()~>#+-=|{}.!'
    return re.sub(f"([{re.escape(escape_chars)}])", r"\\\1", text)

def get_certificate(hostname, port=443):
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    with socket.create_connection((hostname, port), timeout=5) as sock:
        with context.wrap_socket(sock, server_hostname=hostname) as ssock:
            return ssock.getpeercert(binary_form=True)

def format_certificate(cert):
    cert_object = crypto.load_certificate(crypto.FILETYPE_ASN1, cert)
    pem_cert = crypto.dump_certificate(crypto.FILETYPE_PEM, cert_object).decode("utf-8")
    not_before = datetime.strptime(cert_object.get_notBefore().decode("ascii"), "%Y%m%d%H%M%SZ")
    not_after = datetime.strptime(cert_object.get_notAfter().decode("ascii"), "%Y%m%d%H%M%SZ")
    validity = f"Срок действия: {not_before.strftime('%Y.%m.%d')} по {not_after.strftime('%Y.%m.%d')}"
    return pem_cert, validity

# ------------------- HANDLERS -------------------
@bot.message_handler(commands=["start", "help"])
def send_welcome(message):
    logger.info(f"Пользователь {user_info(message)} вызвал {message.text}")
    bot.reply_to(message, "Привет! Отправь мне URL (https://...) и я выгружу SSL-сертификат и его срок действия.")

@bot.message_handler(func=lambda message: message.text.startswith("https://") or message.text.startswith("http://"))
def get_ssl_certificate_handler(message):
    url = message.text.strip()
    logger.info(f"Запрос сертификата: {url} от пользователя {user_info(message)}")
    try:
        parsed_url = urlparse(url)
        hostname = parsed_url.hostname
        port = parsed_url.port or 443

        cert_binary = get_certificate(hostname, port)
        cert_pem, validity = format_certificate(cert_binary)
        pem_safe = escape_markdown(cert_pem)
        validity_safe = escape_markdown(validity)

        bot.send_message(
            message.chat.id,
            f"Сертификат для {escape_markdown(url)}:\n```\n{pem_safe}\n```\n{validity_safe}",
            parse_mode="MarkdownV2"
        )
        logger.info(f"Сертификат успешно выдан: {url}")
    except Exception as e:
        logger.error(f"Ошибка при обработке {url}: {e}", exc_info=True)
        bot.reply_to(message, f"Ошибка при получении сертификата: {e}")

# ------------------- RUN -------------------
if __name__ == "__main__":
    logger.info("SSL бот запущен")
    bot.infinity_polling()
