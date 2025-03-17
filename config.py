# config.py

BOT_TOKEN = "7594100974:AAHktTMVV9xRokpcV42rxjVF77-akEZeoek"  # токен вашего бота
CRYPTO_PAY_TOKEN = "356239:AAyWldQ0Otj4u8y4Gq5Wfsb1hKgwcwwL948"  # токен от aiocryptopay (сеть Test_Net)
LEAK_OSINT_API_KEY = "2022502712:6PdiMM9x"  # токен для Leak Osint API
LEAK_OSINT_API_URL = "https://leakosintapi.com/"

CHANNEL_ID = -1002542736218
CHANNEL_LINK = "https://t.me/+SMNZWOrwRJBlNTBk"
PHOTO_URL = "https://ibb.co/67W6c7WB"  # ссылка на фото приветствия

# Тарифные планы (цена в долларах и продолжительность подписки в днях)
SUB_PLANS = {
    "week": {"price": 1.5, "duration": 7},
    "month": {"price": 3.5, "duration": 30},
    "forever": {"price": 10, "duration": None}  # Бессрочная подписка
}

# Файл для хранения информации о пользователях (JSON база)
USERS_FILE = "users.json"
