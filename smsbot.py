from telethon import TelegramClient, events, Button
import configparser
import os

# Чтение конфигурации
config_file = 'config.data'
if not os.path.exists(config_file):
    print("Ошибка: файл config.data не найден. Пожалуйста, выполните настройку.")
    exit(1)

cpass = configparser.RawConfigParser()
cpass.read(config_file)

try:
    api_id = int(cpass['cred']['id'])
    api_hash = cpass['cred']['hash']
    bot_token = cpass['cred']['token']
except KeyError as e:
    print(f"Ошибка: отсутствует ключ {e} в конфигурации. Проверьте файл config.data.")
    exit(1)

# Создание клиентов
bot = TelegramClient('bot', api_id, api_hash).start(bot_token=bot_token)
client = TelegramClient('user', api_id, api_hash).start()

# Глобальные переменные
dialogs = []
selected_chats_for_broadcast = []
selected_message = None
action = None

# Команда /start
@bot.on(events.NewMessage(pattern="/start"))
async def start(event):
    await event.reply(
        "Привет! Этот бот поможет вам отправлять сообщения в несколько чатов.\n\n"
        "Выберите действие:",
        buttons=[
            [Button.inline("Рассылка", b"broadcast")],
            [Button.inline("Пересылка", b"forward")],
        ]
    )

# Обработка выбора "Рассылка"
@bot.on(events.CallbackQuery(data=b"broadcast"))
async def broadcast_handler(event):
    global action, dialogs
    action = "Рассылка"
    dialogs = await client.get_dialogs()

    chat_list = "Список доступных чатов:\n"
    for i, dialog in enumerate(dialogs, start=1):
        if dialog.is_group or dialog.is_channel:
            chat_list += f"{i}. {dialog.name} (ID: {dialog.id})\n"

    await event.edit(
        chat_list + "\nВведите номера чатов через запятую (например, 1,2,3):",
        buttons=[
            [Button.inline("Назад", b"back")],
        ]
    )

# Обработка выбора "Назад"
@bot.on(events.CallbackQuery(data=b"back"))
async def back_handler(event):
    await start(event)

# Обработка ввода номеров чатов для рассылки
@bot.on(events.NewMessage)
async def chat_selection_handler(event):
    global action, selected_chats_for_broadcast, dialogs, selected_message

    if action == "Рассылка":
        chat_input = event.text.strip()
        try:
            chat_indexes = [int(i) - 1 for i in chat_input.split(",")]
            selected_chats_for_broadcast = [dialogs[i] for i in chat_indexes if 0 <= i < len(dialogs)]
            if not selected_chats_for_broadcast:
                await event.reply("Вы не выбрали ни одного чата. Попробуйте снова.")
                return

            await event.reply("Введите сообщение, которое хотите разослать:")
            action = "Введите сообщение"
        except ValueError:
            await event.reply("Ошибка: пожалуйста, введите корректные номера чатов через запятую (например, 1,2,3).")

    elif action == "Введите сообщение":
        selected_message = event.text.strip()
        if selected_message:
            confirmation_text = "Вы подтверждаете рассылку сообщения в следующие чаты?\n"
            for chat in selected_chats_for_broadcast:
                confirmation_text += f"{chat.name} (ID: {chat.id})\n"

            confirmation_text += f"\nСообщение: {selected_message[:50]}..."  # Ограничим вывод текста до 50 символов

            await event.reply(
                confirmation_text,
                buttons=[
                    [Button.inline("Подтвердить", b"confirm_broadcast")],
                    [Button.inline("Назад", b"back")]
                ]
            )
        else:
            await event.reply("Сообщение не может быть пустым. Пожалуйста, введите текст.")

# Подтверждение рассылки
@bot.on(events.CallbackQuery(data=b"confirm_broadcast"))
async def confirm_broadcast_handler(event):
    global selected_message, selected_chats_for_broadcast

    try:
        for chat in selected_chats_for_broadcast:
            await client.send_message(chat.id, selected_message)
        await event.reply("Сообщение успешно разослано в выбранные чаты!")
    except Exception as e:
        await event.reply(f"Ошибка при рассылке: {str(e)}")

# Команда для пересылки
@bot.on(events.CallbackQuery(data=b"forward"))
async def forward_handler(event):
    global action, dialogs
    action = "Пересылка"
    dialogs = await client.get_dialogs()

    chat_list = "Список доступных чатов:\n"
    for i, dialog in enumerate(dialogs, start=1):
        if dialog.is_group or dialog.is_channel:
            chat_list += f"{i}. {dialog.name} (ID: {dialog.id})\n"

    await event.edit(
        chat_list + "\nВведите номера чатов через запятую для пересылки (например, 1,2,3):",
        buttons=[
            [Button.inline("Назад", b"back")],
        ]
    )

# Обработка пересылки сообщений
@bot.on(events.NewMessage)
async def forward_message_handler(event):
    global action, selected_chats_for_broadcast, dialogs

    if action == "Пересылка":
        try:
            message_to_forward = await client.get_messages(event.chat_id, ids=event.id)
            if not selected_chats_for_broadcast:
                await event.reply("Ошибка: чаты для пересылки не выбраны.")
                return

            for chat in selected_chats_for_broadcast:
                await client.forward_messages(chat.id, message_to_forward)
            await event.reply("Сообщение успешно переслано в выбранные чаты!")
        except Exception as e:
            await event.reply(f"Ошибка при пересылке: {str(e)}")

# Запуск бота
print("Бот запущен. Ожидание команд...")
bot.run_until_disconnected()
