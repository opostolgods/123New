import requests
from bs4 import BeautifulSoup
from telebot import types
import re

def get_tg_channels(query):
    """
    Search for Telegram channels based on a query
    
    Args:
        query (str): The search query
        
    Returns:
        tuple: (list of channel results, search URL)
    """
    url = f"https://tgsearch.org/search?query={'+'.join(query.split())}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7'
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        channel_cards = soup.find_all('div', class_='channel-card')
        results = []
        for card in channel_cards:
            title_element = card.find('h2', class_='channel-card__title').find('a')
            if title_element and title_element.has_attr('href'):
                channel_url = title_element['href']
                channel_name = title_element.get_text(strip=True)
                match = re.search(r'/channel/(\d+)$', channel_url)
                if match:
                    channel_id = match.group(1)
                    channel_page_url = f"https://tgsearch.org/channel/{channel_id}"
                    channel_response = requests.get(channel_page_url, headers=headers, timeout=10)
                    channel_response.raise_for_status()
                    channel_soup = BeautifulSoup(channel_response.content, 'html.parser')
                    channel_link_element = channel_soup.find('a', class_='app', href=True)
                    if channel_link_element:
                        channel_link = channel_link_element['href']
                        results.append({"name": channel_name, "url": channel_link})
                    else:
                        results.append({"name": channel_name, "url": f"https://t.me/c/{channel_id}"})
                else:
                    match = re.search(r'/([a-zA-Z0-9_]+)$', channel_url)
                    if match:
                        channel_username = match.group(1)
                        results.append({"name": channel_name, "url": f"https://t.me/{channel_username}"})
                    else:
                        results.append({"name": channel_name, "url": f"https://tgsearch.org{channel_url}"})
        return results, url
    except requests.exceptions.RequestException as e:
        print(f"Ошибка при запросе: {e}")
        return None, None

def get_channel_invite_link(channel_url):
    """
    Get the invite link for a Telegram channel
    
    Args:
        channel_url (str): The URL of the channel
        
    Returns:
        str: The invite link for the channel
    """
    try:
        response = requests.get(channel_url, timeout=5)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        invite_link = soup.find('a', class_="tgme_action_button_new")
        if invite_link and invite_link.has_attr('href'):
            return invite_link['href']
        return channel_url
    except requests.exceptions.RequestException:
        return channel_url

def send_results(bot, chat_id, results, page, search_url, message_id=None):
    """
    Send search results to the user
    
    Args:
        bot: The Telegram bot instance
        chat_id (int): The chat ID to send the results to
        results (list): The search results
        page (int): The current page of results
        search_url (str): The URL of the search
        message_id (int, optional): The message ID to edit. Defaults to None.
    """
    if not results:
        bot.send_message(chat_id, "<b>❌ Результаты поиска:</b>\n<i>Ничего не найдено</i>", parse_mode='HTML')
        return

    items_per_page = 10
    total_pages = (len(results) + items_per_page - 1) // items_per_page
    page = max(0, min(page, total_pages - 1))
    start_index = page * items_per_page
    end_index = min(start_index + items_per_page, len(results))

    message_text = f"""
    <b>🔎 Результаты поиска</b> ({start_index + 1}-{end_index} из {len(results)}):
    <i>Ссылка на запрос:</i> <a href='{search_url}'>{search_url}</a>
    """
    for i in range(start_index, end_index):
        channel = results[i]
        channel_url = channel["url"]
        if "t.me/c/" in channel_url:
            channel_url = get_channel_invite_link(channel_url)
        message_text += f"\n<b>{i + 1}.</b> <a href='{channel_url}'>{channel['name']}</a>"

    keyboard = types.InlineKeyboardMarkup(row_width=5)
    
    pagination_buttons = []
    if page > 0:
        pagination_buttons.append(types.InlineKeyboardButton("⬅️", callback_data=f"page_{page-1}"))
    else:
        pagination_buttons.append(types.InlineKeyboardButton("⬅️", callback_data="noop"))
    
    for i in range(total_pages):
        if i == page:
            pagination_buttons.append(types.InlineKeyboardButton(f"[{i+1}]", callback_data="noop"))
        else:
            pagination_buttons.append(types.InlineKeyboardButton(str(i+1), callback_data=f"page_{i}"))
    
    if page < total_pages - 1:
        pagination_buttons.append(types.InlineKeyboardButton("➡️", callback_data=f"page_{page+1}"))
    else:
        pagination_buttons.append(types.InlineKeyboardButton("➡️", callback_data="noop"))
    
    keyboard.add(*pagination_buttons)
    
    keyboard.add(types.InlineKeyboardButton(
        "📥 Скачать в TXT", 
        callback_data=f"download_{start_index}_{end_index}"
    ))
    keyboard.add(types.InlineKeyboardButton(
        "🔄 Новый поиск", 
        callback_data="new_search"
    ))

    if message_id:
        bot.edit_message_text(
            message_text,
            chat_id=chat_id,
            message_id=message_id,
            parse_mode='HTML',
            reply_markup=keyboard,
            disable_web_page_preview=True
        )
    else:
        sent_message = bot.send_message(
            chat_id,
            message_text,
            parse_mode='HTML',
            reply_markup=keyboard,
            disable_web_page_preview=True
        )
        return sent_message.message_id

