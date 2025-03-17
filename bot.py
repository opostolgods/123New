import telebot
from telebot import types
import io
import requests
from datetime import datetime, timedelta

from config import BOT_TOKEN, CHANNEL_ID, CHANNEL_LINK, PHOTO_URL, SUB_PLANS, USERS_FILE, LEAK_OSINT_API_KEY, LEAK_OSINT_API_URL
from utils import get_user_profile, update_user_profile, safe_edit_message
from payment import create_invoice, check_invoice, pending_invoices
from html_report import generate_html_report
from ip_search import get_ip_info
from channel import get_tg_channels, send_results

bot = telebot.TeleBot(BOT_TOKEN)
search_results = {}

@bot.message_handler(commands=['start'])
def start_handler(message):
    user_id = message.from_user.id
    try:
        member = bot.get_chat_member(CHANNEL_ID, user_id)
        subscribed = not (member.status in ["left", "kicked"])
    except Exception:
        subscribed = False

    if not subscribed:
        text = "📡 <b>Для использования данного бота нужно подписаться на канал.</b>"
        markup = types.InlineKeyboardMarkup()
        btn_channel = types.InlineKeyboardButton("🌖 Канал", url=CHANNEL_LINK)
        btn_check = types.InlineKeyboardButton("🌑 Проверить", callback_data="check_subscription")
        markup.add(btn_channel, btn_check)
        bot.send_message(message.chat.id, text, parse_mode="HTML", reply_markup=markup)
    else:
        text = f"<b>⭐️ Добро пожаловать {message.from_user.first_name}!</b>\n\n" \
               "<b>🚀 Наши плюсы</b>\n" \
               "<blockquote>» Мультифункциональность\n" \
               "» Дешёвые тарифы\n" \
               "» Постоянные обновления</blockquote>\n\n" \
               "<b>Мы знаем что такое качество</b>"
        markup = types.InlineKeyboardMarkup()
        btn_search = types.InlineKeyboardButton("Поиск", callback_data="search")
        btn_profile = types.InlineKeyboardButton("Профиль", callback_data="profile")
        markup.add(btn_search, btn_profile)
        bot.send_photo(message.chat.id, PHOTO_URL, caption=text, parse_mode="HTML", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "check_subscription")
def check_subscription_callback(call):
    user_id = call.from_user.id
    try:
        member = bot.get_chat_member(CHANNEL_ID, user_id)
        subscribed = not (member.status in ["left", "kicked"])
    except Exception:
        subscribed = False

    if subscribed:
        safe_edit_message(bot, call, "✅ Вы успешно подписались\n\n<blockquote><b>Пропишите команду /start заного</b></blockquote>")
    else:
        bot.answer_callback_query(call.id, "Вы всё ещё не подписаны на канал.")

@bot.callback_query_handler(func=lambda call: call.data == "profile")
def profile_callback(call):
    user_id = call.from_user.id
    profile = get_user_profile(user_id, USERS_FILE)
    sub_status = "отсутствует"
    if profile.get("subscription"):
        if profile["subscription"] == "forever":
            sub_status = "Навсегда"
        else:
            try:
                expiry = datetime.strptime(profile["subscription"], "%Y-%m-%d %H:%M:%S")
                if datetime.now() < expiry:
                    sub_status = f"Активна до {profile['subscription']}"
            except:
                pass
    text = (
        "<b>🖥️ Ваш профиль</b>\n\n"
        "<b>Информация пользователя</b>\n"
        f"<blockquote>💎 Подписка - <code>{sub_status}</code>\n"
        f"👤 Партнёр - <code>{profile.get('partner', 'нет')}</code>\n"
        f"🆔 Айди - <code>{user_id}</code></blockquote>"
    )
    markup = types.InlineKeyboardMarkup()
    btn_sub = types.InlineKeyboardButton("Подписка", callback_data="subscription")
    btn_back = types.InlineKeyboardButton("Назад", callback_data="back_to_main")
    markup.add(btn_sub, btn_back)
    safe_edit_message(bot, call, text, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "back_to_main")
def back_to_main_callback(call):
    text = f"<b>⭐️ Добро пожаловать {call.from_user.first_name}!</b>\n\n" \
           "<b>🚀 Наши плюсы</b>\n" \
           "<blockquote>» Мультифункциональность\n" \
           "» Дешёвые тарифы\n" \
           "» Постоянные обновления</blockquote>\n\n" \
           "<b>Мы знаем что такое качество</b>"
    markup = types.InlineKeyboardMarkup()
    btn_search = types.InlineKeyboardButton("Поиск", callback_data="search")
    btn_profile = types.InlineKeyboardButton("Профиль", callback_data="profile")
    markup.add(btn_search, btn_profile)
    safe_edit_message(bot, call, text, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "subscription")
def subscription_callback(call):
    text = "<b>Выберите тарифный план</b>"
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn_week = types.InlineKeyboardButton("Неделя - 1.5 $", callback_data="sub_week")
    btn_month = types.InlineKeyboardButton("Месяц - 3.5 $", callback_data="sub_month")
    btn_forever = types.InlineKeyboardButton("Навсегда - 10 $", callback_data="sub_forever")
    btn_back = types.InlineKeyboardButton("Назад", callback_data="back_to_main")
    markup.add(btn_week, btn_month)
    markup.add(btn_forever, btn_back)
    safe_edit_message(bot, call, text, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("sub_"))
def sub_plan_callback(call):
    user_id = call.from_user.id
    plan = call.data.split("_")[1]
    plan_info = SUB_PLANS.get(plan)
    if not plan_info:
        bot.answer_callback_query(call.id, "Неверный тарифный план.")
        return
    price = plan_info["price"]
    try:
        invoice = create_invoice("USDT", price)
    except Exception as e:
        bot.answer_callback_query(call.id, f"Ошибка создания счёта: {str(e)}")
        return
    pending_invoices[user_id] = {
        "invoice_id": invoice.invoice_id,
        "plan": plan
    }
    text = (
        f"<b>Выбранный тариф:</b> <code>{plan}</code>\n"
        f"<b>Цена:</b> <code>{price} $</code>\n\n"
        "<b>После оплаты нажмите кнопку проверить.</b>"
    )
    markup = types.InlineKeyboardMarkup()
    btn_invoice = types.InlineKeyboardButton("Счёт", url=invoice.pay_url)
    btn_check = types.InlineKeyboardButton("Проверить", callback_data="check_payment")
    markup.add(btn_invoice, btn_check)
    safe_edit_message(bot, call, text, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "check_payment")
def check_payment_callback(call):
    user_id = call.from_user.id
    if user_id not in pending_invoices:
        bot.answer_callback_query(call.id, "Счёт не найден. Попробуйте создать новый.")
        return
    invoice_id = pending_invoices[user_id]["invoice_id"]
    plan = pending_invoices[user_id]["plan"]
    invoice = check_invoice(invoice_id)
    if invoice is None:
        bot.answer_callback_query(call.id, "Ошибка проверки оплаты.")
        return
    if invoice.status == 'active':
        bot.answer_callback_query(call.id, "Оплата не обнаружена, попробуйте позже.")
    elif invoice.status == 'paid':
        if plan == "forever":
            expiry_str = "forever"
        else:
            expiry_date = datetime.now() + timedelta(days=SUB_PLANS[plan]["duration"])
            expiry_str = expiry_date.strftime("%Y-%m-%d %H:%M:%S")
        profile = get_user_profile(user_id, USERS_FILE)
        profile["subscription"] = expiry_str
        update_user_profile(user_id, profile, USERS_FILE)
        safe_edit_message(bot, call, "Оплата успешно прошла, подписка выдана")
        pending_invoices.pop(user_id, None)
    else:
        bot.answer_callback_query(call.id, "Не удалось определить статус оплаты.")

@bot.callback_query_handler(func=lambda call: call.data == "search")
def search_callback(call):
    user_id = call.from_user.id
    profile = get_user_profile(user_id, USERS_FILE)
    sub_active = False
    if profile.get("subscription"):
        if profile["subscription"] == "forever":
            sub_active = True
        else:
            try:
                expiry = datetime.strptime(profile["subscription"], "%Y-%m-%d %H:%M:%S")
                if datetime.now() < expiry:
                    sub_active = True
            except:
                sub_active = False
    if not sub_active:
        safe_edit_message(bot, call, "Купите подписку для доступа к поиску.")
    else:
        text = "<b>Выберите направление поиска 🔎</b>"
        markup = types.InlineKeyboardMarkup(row_width=2)
        btn_ip = types.InlineKeyboardButton("Айпи", callback_data="search_ip")
        btn_probiv = types.InlineKeyboardButton("Пробив", callback_data="search_probiv")
        btn_channel = types.InlineKeyboardButton("Каналы", callback_data="search_channel")
        btn_telegraph = types.InlineKeyboardButton("Телеграф", callback_data="search_telegraph")
        markup.add(btn_ip, btn_probiv, btn_channel, btn_telegraph)
        safe_edit_message(bot, call, text, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "search_ip")
def search_ip_callback(call):
    text = "<b>Введите айпи для поиска</b>"
    safe_edit_message(bot, call, text)
    bot.register_next_step_handler_by_chat_id(call.message.chat.id, process_ip_search)

def process_ip_search(message):
    ip = message.text.strip()
    if not ip:
        bot.send_message(message.chat.id, "Пустой запрос. Попробуйте снова.")
        return
    
    try:
        ip_info = get_ip_info(ip)
        if ip_info and ip_info.get("status") == "success":
            result = f"""\`\`\`
IP: {ip_info.get('query', 'Н/Д')}
Страна: {ip_info.get('country', 'Н/Д')} ({ip_info.get('countryCode', 'Н/Д')})
Регион: {ip_info.get('regionName', 'Н/Д')} ({ip_info.get('region', 'Н/Д')})
Город: {ip_info.get('city', 'Н/Д')}
Почтовый индекс: {ip_info.get('zip', 'Н/Д')}
Координаты: {ip_info.get('lat', 'Н/Д')}, {ip_info.get('lon', 'Н/Д')}
Часовой пояс: {ip_info.get('timezone', 'Н/Д')}
Провайдер: {ip_info.get('isp', 'Н/Д')}
Организация: {ip_info.get('org', 'Н/Д')}
AS: {ip_info.get('as', 'Н/Д')}
\`\`\`"""
            bot.send_message(message.chat.id, result, parse_mode="Markdown")
        else:
            bot.send_message(message.chat.id, f"Ошибка при поиске информации по IP: {ip_info.get('message', 'Неизвестная ошибка')}")
    except Exception as e:
        bot.send_message(message.chat.id, f"Произошла ошибка: {str(e)}")

@bot.callback_query_handler(func=lambda call: call.data == "search_probiv")
def search_probiv_callback(call):
    text = "<b>Введите запрос для поиска</b>"
    safe_edit_message(bot, call, text)
    bot.register_next_step_handler_by_chat_id(call.message.chat.id, do_search)

def do_search(message):
    query = message.text.strip()
    if not query:
        bot.send_message(message.chat.id, "Пустой запрос. Попробуйте снова.")
        return
    data = {
        "token": LEAK_OSINT_API_KEY,
        "request": query,
        "limit": 100,
        "lang": "ru"
    }
    try:
        response = requests.post(LEAK_OSINT_API_URL, json=data, timeout=10)
        if response.status_code == 200:
            api_data = response.json()
        else:
            bot.send_message(message.chat.id, f"Ошибка API:\nКод: {response.status_code}\nОтвет: {response.text}")
            return
    except Exception as e:
        bot.send_message(message.chat.id, f"Сетевая ошибка: {str(e)}")
        return
    html_report = generate_html_report(api_data)
    file_bytes = html_report.encode("utf-8")
    file_obj = io.BytesIO(file_bytes)
    file_obj.name = "result.html"
    bot.send_document(message.chat.id, file_obj, caption="Результат поиска", parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: call.data == "search_channel")
def search_channel_callback(call):
    text = "<b>Введите название канала для поиска</b>"
    safe_edit_message(bot, call, text)
    bot.register_next_step_handler_by_chat_id(call.message.chat.id, process_channel_search)

def process_channel_search(message):
    query = message.text.strip()
    if not query:
        bot.send_message(message.chat.id, "Пустой запрос. Попробуйте снова.")
        return
    
    bot.send_message(message.chat.id, "⏳ Ищем каналы...")
    results, search_url = get_tg_channels(query)
    if results:
        search_results[message.chat.id] = {
            "results": results,
            "page": 0,
            "search_url": search_url,
            "message_id": None
        }
        send_results(bot, message.chat.id, results, 0, search_url)
    else:
        bot.send_message(
            message.chat.id,
            "<b>❌ Ошибка:</b> <i>Каналы не найдены</i>",
            parse_mode='HTML'
        )

@bot.callback_query_handler(func=lambda call: call.data == "search_telegraph")
def search_telegraph_callback(call):
    bot.answer_callback_query(call.id)
    bot.send_message(call.message.chat.id, "api error 200")

@bot.callback_query_handler(func=lambda call: call.data.startswith("page_"))
def handle_page_change(call):
    if call.message.chat.id not in search_results:
        bot.answer_callback_query(call.id, "Начните поиск сначала")
        return

    page = int(call.data.split("_")[1])
    data = search_results[call.message.chat.id]
    send_results(
        bot,
        call.message.chat.id,
        data["results"],
        page,
        data["search_url"],
        call.message.message_id
    )
    search_results[call.message.chat.id]["page"] = page
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data == "noop")
def handle_noop(call):
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data.startswith("download_"))
def handle_download(call):
    if call.message.chat.id not in search_results:
        bot.answer_callback_query(call.id, "Начните поиск сначала")
        return

    _, start_index, end_index = call.data.split("_")
    start_index, end_index = int(start_index), int(end_index)
    results = search_results[call.message.chat.id]["results"]
    
    txt_content = ""
    for i in range(start_index, end_index):
        channel = results[i]
        txt_content += f"{i + 1}. {channel['name']} - {channel['url']}\n"
    
    file_obj = io.BytesIO(txt_content.encode('utf-8'))
    file_obj.name = "channels.txt"
    
    bot.send_document(
        call.message.chat.id,
        document=file_obj,
        caption=f"📋 Список каналов ({start_index + 1}-{end_index})"
    )
    bot.answer_callback_query(call.id, "✅ Файл отправлен!")

@bot.callback_query_handler(func=lambda call: call.data == "new_search")
def handle_new_search(call):
    if call.message.chat.id in search_results:
        del search_results[call.message.chat.id]
    
    text = "<b>Выберите направление поиска 🔎</b>"
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn_ip = types.InlineKeyboardButton("Айпи", callback_data="search_ip")
    btn_probiv = types.InlineKeyboardButton("Пробив", callback_data="search_probiv")
    btn_channel = types.InlineKeyboardButton("Каналы", callback_data="search_channel")
    btn_telegraph = types.InlineKeyboardButton("Телеграф", callback_data="search_telegraph")
    markup.add(btn_ip, btn_probiv, btn_channel, btn_telegraph)
    safe_edit_message(bot, call, text, reply_markup=markup)

bot.polling(non_stop=True)

