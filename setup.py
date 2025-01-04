#!/bin/env python3

"""
You can rerun setup.py if you have added some wrong value.
"""

re = "\033[1;31m"
gr = "\033[1;32m"
cy = "\033[1;36m"

import os, sys
import time
import configparser
from telethon import TelegramClient

def banner():
    os.system('clear')
    print(f"""
    {re}╔═╗{cy}┌─┐┌┬┐┬ ┬┌─┐
    {re}╚═╗{cy}├┤  │ │ │├─┘
    {re}╚═╝{cy}└─┘ ┴ └─┘┴
    """)

def requirements():
    def csv_lib():
        banner()
        print(gr + '[' + cy + '+' + gr + ']' + cy + ' This may take some time ...')
        os.system("""
            pip3 install cython numpy pandas
            python3 -m pip install cython numpy pandas
            """)
    banner()
    print(gr + '[' + cy + '+' + gr + ']' + cy + ' It will take up to 10 min to install CSV merge.')
    input_csv = input(gr + '[' + cy + '+' + gr + ']' + cy + ' Do you want to enable CSV merge (y/n): ').lower()
    if input_csv == "y":
        csv_lib()
    else:
        pass
    print(gr + "[+] Installing requirements ...")
    os.system("""
        pip3 install telethon requests configparser
        python3 -m pip install telethon requests configparser
        touch config.data
        """)
    banner()
    print(gr + "[+] Requirements installed.\n")


def config_setup():
    banner()
    cpass = configparser.RawConfigParser()
    cpass.add_section('cred')
    
    # Запрос API ID и Hash
    xid = input(gr + "[+] Enter API ID: " + re)
    cpass.set('cred', 'id', xid)
    xhash = input(gr + "[+] Enter hash ID: " + re)
    cpass.set('cred', 'hash', xhash)
    xphone = input(gr + "[+] Enter phone number: " + re)
    cpass.set('cred', 'phone', xphone)
    
    # Запрос для токена бота
    xtoken = input(gr + "[+] Enter bot token: " + re)
    cpass.set('cred', 'token', xtoken)
    
    # Запись конфигурации в файл
    try:
        with open('config.data', 'w') as setup:
            cpass.write(setup)
        print(gr + "[+] Setup complete!")
    except Exception as e:
        print(gr + "[" + re + "!" + gr + "] Error while saving config: " + str(e))


def merge_csv():
    import pandas as pd
    import sys
    banner()
    if len(sys.argv) < 4:
        print(gr + '[' + cy + '+' + gr + ']' + cy + ' Missing files to merge. Usage: python3 setup.py -m file1.csv file2.csv')
        return
    file1 = pd.read_csv(sys.argv[2])
    file2 = pd.read_csv(sys.argv[3])
    print(gr + '[' + cy + '+' + gr + ']' + cy + f' Merging {sys.argv[2]} & {sys.argv[3]} ...')
    print(gr + '[' + cy + '+' + gr + ']' + cy + ' Big files can take some time ... ')
    merge = file1.merge(file2, on='username')
    merge.to_csv("output.csv", index=False)
    print(gr + '[' + cy + '+' + gr + ']' + cy + ' Saved file as "output.csv"\n')

def update_tool():
    import requests as r
    banner()
    source = r.get("https://raw.githubusercontent.com/th3unkn0n/TeleGram-Scraper/master/.image/.version")
    if source.text.strip() == '3':
        print(gr + '[' + cy + '+' + gr + ']' + cy + ' Already latest version')
    else:
        print(gr + '[' + cy + '+' + gr + ']' + cy + ' Removing old files ...')
        os.system('rm *.py')
        time.sleep(3)
        print(gr + '[' + cy + '+' + gr + ']' + cy + ' Getting latest files ...')
        os.system("""
            curl -s -O https://raw.githubusercontent.com/th3unkn0n/TeleGram-Scraper/master/add2group.py
            curl -s -O https://raw.githubusercontent.com/th3unkn0n/TeleGram-Scraper/master/scraper.py
            curl -s -O https://raw.githubusercontent.com/th3unkn0n/TeleGram-Scraper/master/setup.py
            curl -s -O https://raw.githubusercontent.com/th3unkn0n/TeleGram-Scraper/master/smsbot.py
            chmod 777 *.py
            """)
        time.sleep(3)
        print(gr + '\n[' + cy + '+' + gr + ']' + cy + ' Update complete.\n')

def run_bot():
    # Чтение данных из конфигурационного файла
    try:
        cpass = configparser.RawConfigParser()
        cpass.read('config.data')
        api_id = cpass['cred']['id']
        api_hash = cpass['cred']['hash']
        phone = cpass['cred']['phone']
        token = cpass['cred']['token']  # Чтение токена

        # Инициализация бота с использованием токена
        bot = TelegramClient('bot', api_id, api_hash).start(bot_token=token)
        print(gr + "[+] Bot started with token:", token)
        bot.run_until_disconnected()
    except Exception as e:
        print(gr + "[" + re + "!" + gr + "] Error while starting bot: " + str(e))


if __name__ == "__main__":
    try:
        if len(sys.argv) > 1:
            if any([sys.argv[1] == '--config', sys.argv[1] == '-c']):
                print(gr + '[' + cy + '+' + gr + ']' + cy + ' Selected module: ' + re + sys.argv[1])
                config_setup()
            elif any([sys.argv[1] == '--merge', sys.argv[1] == '-m']):
                print(gr + '[' + cy + '+' + gr + ']' + cy + ' Selected module: ' + re + sys.argv[1])
                merge_csv()
            elif any([sys.argv[1] == '--update', sys.argv[1] == '-u']):
                print(gr + '[' + cy + '+' + gr + ']' + cy + ' Selected module: ' + re + sys.argv[1])
                update_tool()
            elif any([sys.argv[1] == '--install', sys.argv[1] == '-i']):
                requirements()
            elif any([sys.argv[1] == '--run-bot', sys.argv[1] == '-r']):
                print(gr + '[' + cy + '+' + gr + ']' + cy + ' Selected module: ' + re + sys.argv[1])
                run_bot()
            elif any([sys.argv[1] == '--help', sys.argv[1] == '-h']):
                banner()
                print("""$ python3 setup.py -m file1.csv file2.csv
                
    ( --config  / -c ) setup API configuration
    ( --merge   / -m ) merge 2 .csv files into one
    ( --update  / -u ) update tool to latest version
    ( --install / -i ) install requirements
    ( --run-bot / -r ) run the bot
    ( --help    / -h ) show this message
                """)
            else:
                print('\n' + gr + '[' + re + '!' + gr + ']' + cy + ' Unknown argument: ' + sys.argv[1])
                print(gr + '[' + re + '!' + gr + ']' + cy + ' For help use: ')
                print(gr + '$ python3 setup.py -h' + '\n')
        else:
            print('\n' + gr + '[' + re + '!' + gr + ']' + cy + ' No argument given.')
            print(gr + '[' + re + '!' + gr + ']' + cy + ' For help use: ')
            print(gr + '$ python3 setup.py -h' + '\n')
    except Exception as e:
        print(gr + '[' + re + '!' + gr + ']' + cy + f' An error occurred: {e}')
