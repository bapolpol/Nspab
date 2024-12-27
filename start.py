from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters, ConversationHandler
from telethon import TelegramClient
import logging
import configparser
import os

# Включаем логирование для отладки
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Статусы для разговора
CHOOSING_CHANNEL, CHOOSING_MESSAGE = range(1, 3)

# Пути к файлам конфигурации
CONFIG_FILE = "config.data"

# Список доступных каналов (обновляем динамически после подключения аккаунта)
CHANNELS = {}

# Инициализация Telethon клиента
def init_telethon_client():
    if not os.path.exists(CONFIG_FILE):
        logger.error("Файл конфигурации не найден. Настройте API с помощью команды /setup.")
        return None

    cpass = configparser.RawConfigParser()
    cpass.read(CONFIG_FILE)

    api_id = cpass.get('cred', 'id')
    api_hash = cpass.get('cred', 'hash')
    phone = cpass.get('cred', 'phone')

    client = TelegramClient('session_name', api_id, api_hash)
    client.connect()

    if not client.is_user_authorized():
        client.send_code_request(phone)
        logger.error("Аккаунт не авторизован. Войдите с помощью Telethon.")
        return None

    return client

def update_channels(client):
    global CHANNELS
    try:
        dialogs = client.get_dialogs()
        CHANNELS = {dialog.title: dialog.entity.id for dialog in dialogs if dialog.is_channel}
    except Exception as e:
        logger.error(f"Ошибка при обновлении списка каналов: {e}")

# Телеграм-бот на Python Telegram Bot
updater = None

def start(update: Update, context):
    """Приветственное сообщение при запуске бота"""
    update.message.reply_text(
        "Привет! Я ваш помощник.
"
        "Настройте аккаунт через /setup или выберите действие ниже:",
        reply_markup=main_menu_keyboard()
    )

def main_menu_keyboard():
    """Создание клавиатуры с кнопками"""
    keyboard = [
        [InlineKeyboardButton("СПАМ", callback_data='spam')],
    ]
    return InlineKeyboardMarkup(keyboard)

# СПАМ функционал
def spam_action(update: Update, context):
    """Обработка кнопки СПАМ"""
    client = init_telethon_client()
    if not client:
        update.callback_query.message.reply_text("Сначала настройте аккаунт через /setup.")
        return ConversationHandler.END

    update_channels(client)

    query = update.callback_query
    query.answer()
    keyboard = [[InlineKeyboardButton(channel, callback_data=f'channel_{i}')] for i, channel in enumerate(CHANNELS.keys())]
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text(text="Выберите группу для отправки:", reply_markup=reply_markup)
    return CHOOSING_CHANNEL

def channel_chosen(update: Update, context):
    """Обработка выбора группы"""
    query = update.callback_query
    channel_index = int(query.data.split('_')[1])
    selected_channel = list(CHANNELS.keys())[channel_index]
    context.user_data['selected_channel'] = selected_channel
    query.answer()
    query.edit_message_text(text=f"Вы выбрали группу: {selected_channel}\nВведите сообщение для отправки:")
    return CHOOSING_MESSAGE

def handle_message(update: Update, context):
    """Обработка введенного сообщения"""
    user_message = update.message.text
    selected_channel = context.user_data.get('selected_channel')

    client = init_telethon_client()
    if not client:
        update.message.reply_text("Сначала настройте аккаунт через /setup.")
        return ConversationHandler.END

    chat_id = CHANNELS[selected_channel]

    # Отправка сообщения в группу
    try:
        with client:
            client.send_message(chat_id, user_message)
        update.message.reply_text(f"Сообщение успешно отправлено в группу '{selected_channel}'.")
    except Exception as e:
        logger.error(f"Ошибка отправки сообщения: {e}")
        update.message.reply_text(f"Не удалось отправить сообщение в группу '{selected_channel}'.")

    update.message.reply_text("Что дальше?", reply_markup=main_menu_keyboard())
    return ConversationHandler.END

def setup(update: Update, context):
    """Настройка API через Telegram Bot"""
    update.message.reply_text("Введите API ID:")
    return process_api_id

def process_api_id(update: Update, context):
    api_id = update.message.text
    context.user_data['api_id'] = api_id
    update.message.reply_text("Введите Hash ID:")
    return process_hash_id

def process_hash_id(update: Update, context):
    api_hash = update.message.text
    context.user_data['api_hash'] = api_hash
    update.message.reply_text("Введите номер телефона:")
    return save_config

def save_config(update: Update, context):
    phone = update.message.text
    api_id = context.user_data['api_id']
    api_hash = context.user_data['api_hash']

    cpass = configparser.RawConfigParser()
    cpass.add_section('cred')
    cpass.set('cred', 'id', api_id)
    cpass.set('cred', 'hash', api_hash)
    cpass.set('cred', 'phone', phone)

    with open(CONFIG_FILE, 'w') as setup:
        cpass.write(setup)

    update.message.reply_text("Конфигурация сохранена! Вы можете использовать команду /start для работы с ботом.")
    return ConversationHandler.END

# Основной метод
if __name__ == '__main__':
    updater = Updater("7654163179:AAHFxQUX9NL4wBjuGKQ5BvknHZXGqznsA6c", use_context=True)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("setup", setup))

    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(spam_action, pattern='spam')],
        states={
            CHOOSING_CHANNEL: [CallbackQueryHandler(channel_chosen, pattern='channel_')],
            CHOOSING_MESSAGE: [MessageHandler(Filters.text & ~Filters.command, handle_message)],
        },
        fallbacks=[],
    )
    dispatcher.add_handler(conv_handler)

    updater.start_polling()
    updater.idle()
