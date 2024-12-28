#!/bin/env python3
from telethon.sync import TelegramClient
from telethon.errors.rpcerrorlist import PeerFloodError, ChannelPrivateError, ChatWriteForbiddenError, SessionPasswordNeededError
import configparser
import os
import sys
import time
from threading import Event

re = "\033[1;31m"
gr = "\033[1;32m"
cy = "\033[1;36m"

stop_event = Event()  # Событие для остановки отправки

class main:

    @staticmethod
    def banner():
        print(f"""
    {re}╔╦╗{cy}┌─┐┌─┐┌─┐┌─┐┬─┐{re}╔═╗
    {re} ║ {cy}├─┐├┤ ├─┘├─┤├┬┘{re}╚═╗
    {re} ╩ {cy}└─┘└─┘┴  ┴ ┴┴└─{re}╚═╝
    by https://github.com/elizhabs
            """)

    @staticmethod
    def send_sms():
        try:
            cpass = configparser.RawConfigParser()
            cpass.read('config.data')
            api_id = cpass['cred']['id']
            api_hash = cpass['cred']['hash']
            phone = cpass['cred']['phone']
        except KeyError:
            os.system('clear')
            main.banner()
            print(re + "[!] run python3 setup.py first !!\n")
            sys.exit(1)

        client = TelegramClient(phone, api_id, api_hash)

        client.connect()
        if not client.is_user_authorized():
            client.send_code_request(phone)
            os.system('clear')
            main.banner()
            try:
                client.sign_in(phone, input(gr + '[+] Enter the code: ' + re))
            except SessionPasswordNeededError:
                # Обработка двухэтапной аутентификации
                password = input(gr + "[+] Two-step verification enabled. Enter your password: " + re)
                client.sign_in(password=password)

        os.system('clear')
        main.banner()

        while True:
            # Выбор чата
            while True:
                print(gr + "[+] Choose a chat (or type '/new' to refresh, '/stop' to restart):")
                dialogs = client.get_dialogs()
                for i, dialog in enumerate(dialogs):
                    if dialog.is_group or dialog.is_channel:
                        print(f"{i + 1}. {dialog.name}")

                user_input = input(gr + "Select a chat by number: " + re).strip()
                if user_input == '/stop':
                    print(gr + "[+] Restarting process...")
                    continue
                elif user_input == '/new':
                    print(gr + "[+] Refreshing chats...")
                    continue
                elif user_input.isdigit():
                    chat_index = int(user_input) - 1
                    if 0 <= chat_index < len(dialogs):
                        chat = dialogs[chat_index]
                        break
                    else:
                        print(re + "[!] Invalid chat number. Try again.")
                else:
                    print(re + "[!] Invalid input. Try again.")

            # Выбор сообщения
            while True:
                messages = client.get_messages(chat.id, limit=10)
                print(gr + "[+] Choose a message to forward (or type '/new' to refresh, '/stop' to restart):")
                for idx, msg in enumerate(messages):
                    if msg.text:
                        print(f"{idx + 1}: {msg.text[:50]}...")
                    else:
                        print(f"{idx + 1}: [Non-text message]")

                user_input = input(gr + "Select message number: " + re).strip()
                if user_input == '/stop':
                    print(gr + "[+] Restarting process...")
                    break
                elif user_input == '/new':
                    print(gr + "[+] Refreshing messages...")
                    continue
                elif user_input.isdigit():
                    msg_index = int(user_input) - 1
                    if 0 <= msg_index < len(messages):
                        message_to_forward = messages[msg_index]
                        break
                    else:
                        print(re + "[!] Invalid message number. Try again.")
                else:
                    print(re + "[!] Invalid input. Try again.")
            else:
                continue  # Если пользователь ввел '/stop', возвращаемся к выбору чата
            break  # Если сообщение выбрано, выходим из цикла выбора сообщения

            # Выбор чатов для пересылки
            while True:
                print(gr + "[+] Choose chats for forwarding (comma-separated, or type '/stop' to restart):")
                for i, dialog in enumerate(dialogs):
                    if dialog.is_group or dialog.is_channel:
                        print(f"{i + 1}. {dialog.name}")

                user_input = input(gr + "Enter chat numbers: " + re).strip()
                if user_input == '/stop':
                    print(gr + "[+] Restarting process...")
                    break
                chat_indices = user_input.split(",")
                try:
                    selected_chats = [
                        dialogs[int(idx.strip()) - 1] for idx in chat_indices if idx.strip().isdigit()
                    ]
                    if selected_chats:
                        break
                    else:
                        print(re + "[!] No valid chats selected. Try again.")
                except (IndexError, ValueError):
                    print(re + "[!] Invalid input. Try again.")
            else:
                continue  # Если '/stop', возвращаемся к выбору чата

            # Выбор интервала ожидания
            interval_minutes = int(input(gr + "Enter the interval in minutes between sending messages: " + re))
            interval_seconds = interval_minutes * 60

            print(gr + f"[+] Messages will be sent every {interval_minutes} minutes. Type '/stop' to interrupt.")

            # Цикл отправки сообщений
            while not stop_event.is_set():
                for forward_chat in selected_chats:
                    try:
                        print(gr + f"[+] Forwarding message to: {forward_chat.name}")
                        client.forward_messages(forward_chat.id, message_to_forward.id, chat.id)
                    except PeerFloodError:
                        print(re + "[!] Getting Flood Error from Telegram. Stopping script. Try again later.")
                        client.disconnect()
                        sys.exit()
                    except ChannelPrivateError:
                        print(re + f"[!] Cannot forward to {forward_chat.name}. Skipping...")
                        continue
                    except ChatWriteForbiddenError:
                        print(re + f"[!] Cannot write in {forward_chat.name}. Skipping...")
                        continue
                    except Exception as e:
                        print(re + f"[!] Error while forwarding to {forward_chat.name}: {e}")
                        continue

                print(gr + f"[+] Waiting {interval_minutes} minutes before the next forwarding...")
                time.sleep(interval_seconds)  # Ожидание

                # Проверка на ввод команды /stop
                print(gr + "[+] Type '/stop' to interrupt or press Enter to continue.")
                if input().strip() == '/stop':
                    stop_event.set()

            print(gr + "[+] Stopped by user. Restarting...")
            stop_event.clear()

if __name__ == "__main__":
    main.send_sms()
