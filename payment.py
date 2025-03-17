# payment.py
import asyncio
from config import CRYPTO_PAY_TOKEN
from aiocryptopay import AioCryptoPay, Networks

# Инициализация клиента для криптоплатежей
crypto = AioCryptoPay(token=CRYPTO_PAY_TOKEN, network=Networks.MAIN_NET)
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

# Словарь ожидающих оплат: ключ – user_id, значение – данные счета и выбранный тариф
pending_invoices = {}

def create_invoice(asset, amount):
    """Создает счет через aiocryptopay."""
    return loop.run_until_complete(crypto.create_invoice(asset=asset, amount=amount))

def check_invoice(invoice_id):
    """Проверяет статус счета."""
    inv_list = loop.run_until_complete(crypto.get_invoices(invoice_ids=[invoice_id]))
    if inv_list:
        return inv_list[0]
    return None
