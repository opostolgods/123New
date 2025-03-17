# utils.py
import os
import json
from datetime import datetime
from telebot import types

def load_data(filename):
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except Exception:
                return {}
    return {}

def save_data(filename, data):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_user_profile(user_id, users_file):
    users = load_data(users_file)
    user_str = str(user_id)
    if user_str not in users:
        users[user_str] = {
            "subscription": None,  # Дата окончания подписки или "forever"
            "partner": "нет"
        }
        save_data(users_file, users)
    return users[user_str]

def update_user_profile(user_id, profile, users_file):
    users = load_data(users_file)
    users[str(user_id)] = profile
    save_data(users_file, users)

def safe_edit_message(bot, call, text, reply_markup=None):
    """Безопасно редактирует сообщение, в зависимости от типа сообщения."""
    if call.message.content_type == 'photo':
        try:
            bot.edit_message_caption(
                caption=text,
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                parse_mode="HTML",
                reply_markup=reply_markup
            )
        except Exception as e:
            print("Ошибка edit_message_caption:", e)
    else:
        try:
            bot.edit_message_text(
                text,
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                parse_mode="HTML",
                reply_markup=reply_markup
            )
        except Exception as e:
            print("Ошибка edit_message_text:", e)
