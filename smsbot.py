from telethon import TelegramClient, events, Button
import configparser

# Чтение конфигурации
cpass = configparser.RawConfigParser()
cpass.read('config.data')

api_id = cpass['cred']['id']
api_hash = cpass['cred']['hash']
bot_token = cpass['cred']['token']

# Создание клиентов
bot = TelegramClient('bot', api_id, api_hash).start(bot_token=bot_token)
client = TelegramClient('user', api_id, api_hash).start()

# Глобальные переменные
dialogs = []
selected_chats_for_broadcast = []  # Список выбранных чатов для рассылки
selected_message = None
action = None  # Действие: 'Рассылка' или 'Пересылка'

# Команда /start
@bot.on(events.NewMessage(pattern="/start"))
async def start(event):
    await event.reply(
        "Выберите действие:",
        buttons=[
            [Button.inline("Рассылка", b"broadcast")],
            [Button.inline("Пересылка", b"forward")],
        ]
    )

# Обработка выбора действия (Рассылка)
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
        chat_list + "\nВведите номер чата для выбора (или через запятую) или нажмите 'Назад'.",
        buttons=[
            [Button.inline("Назад", b"back")],
        ]
    )

# Обработка выбора действия (Пересылка)
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
        chat_list + "\nВведите номер чата для выбора или нажмите 'Назад'.",
        buttons=[
            [Button.inline("Назад", b"back")],
        ]
    )

# Кнопка "Назад"
@bot.on(events.CallbackQuery(data=b"back"))
async def back_handler(event):
    await start(event)

# Обработка ввода номера чата для рассылки
@bot.on(events.NewMessage)
async def chat_selection_handler(event):
    global action, selected_chats_for_broadcast, dialogs, selected_message

    # Если выбрали "Рассылку", то обрабатываем ввод чатов
    if action == "Рассылка":
        chat_input = event.text.strip()
        if chat_input:  # Если введен текст
            chat_indexes = chat_input.split(",")  # Разделяем по запятой или тире
            selected_chats_for_broadcast.clear()  # Очищаем предыдущие выборы

            # Перебираем чаты по номерам
            for index in chat_indexes:
                try:
                    chat_index = int(index.strip()) - 1
                    if 0 <= chat_index < len(dialogs):
                        selected_chats_for_broadcast.append(dialogs[chat_index])
                    else:
                        await event.reply(f"Чат с номером {index} не найден.")
                except ValueError:
                    await event.reply("Ошибка: Введите корректные номера чатов.")

            if selected_chats_for_broadcast:
                # Запрашиваем текст сообщения
                await event.reply("Теперь введите текст сообщения для рассылки:")
                action = "Введите сообщение"  # Меняем действие на ввод сообщения
            else:
                await event.reply("Вы не выбрали чаты. Попробуйте снова.")

    # Если выбрали "Пересылку", то обрабатываем выбор сообщения
    elif action == "Пересылка":
        if event.text.isdigit():
            chat_index = int(event.text.strip()) - 1
            if 0 <= chat_index < len(dialogs):
                selected_chat = dialogs[chat_index]
                messages = await client.get_messages(selected_chat, limit=5)
                message_list = "Выберите сообщение для пересылки:\n"
                for i, msg in enumerate(messages, start=1):
                    text_preview = msg.text[:50] if msg.text else "[Медиа]"
                    message_list += f"{i}. {text_preview}\n"
                
                await event.reply(message_list + "\nВведите номер сообщения для пересылки или нажмите 'Назад'.", buttons=[Button.inline("Назад", b"back")])
            else:
                await event.reply("Неверный номер чата. Попробуйте снова.")
        else:
            await event.reply("Пожалуйста, выберите правильный номер чата для пересылки.")

    elif action == "Введите сообщение":
        selected_message = event.text.strip()
        confirmation_text = "Вы подтверждаете рассылку в следующие чаты?\n"
        for chat in selected_chats_for_broadcast:
            confirmation_text += f"{chat.name} (ID: {chat.id})\n"

        confirmation_text += f"\nСообщение: {selected_message[:50]}..."

        await event.reply(
            confirmation_text + "\n\nНажмите 'Подтвердить' для рассылки или 'Назад' для отмены.",
            buttons=[
                [Button.inline("Подтвердить", b"confirm_broadcast")],
                [Button.inline("Назад", b"back")]
            ]
        )

# Подтверждение рассылки
@bot.on(events.CallbackQuery(data=b"confirm_broadcast"))
async def confirm_broadcast_handler(event):
    global selected_message, selected_chats_for_broadcast

    try:
        for chat in selected_chats_for_broadcast:
            await client.send_message(chat.id, selected_message)
        await event.reply("Сообщение успешно разослано во все выбранные чаты!")
    except Exception as e:
        await event.reply(f"Ошибка при рассылке: {str(e)}")

# Запуск бота
print("Бот запущен и готов к работе!")
bot.run_until_disconnected()
