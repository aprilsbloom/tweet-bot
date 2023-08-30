import os
import json
from datetime import datetime

def write_data(data):
    with open('config.json', 'w', encoding='utf8') as file:
        file.write(json.dumps(data, indent=4))

def fetch_data():
    temp_config = {
        "discord": {
            "token": "",
            "authed_users": [],
            "emojis": {}
        },
        "twitter": {
            "consumer_key": "",
            "consumer_secret": "",
            "access_token": "",
            "access_token_secret": "",
            "bearer_token": ""
        }
    }

    try:
        with open('config.json', 'r', encoding='utf8') as file:
            temp_config.update(json.load(file))
            write_data(temp_config)
            return temp_config

    except (FileNotFoundError, json.decoder.JSONDecodeError):
        log.info('Config file not found! Creating one')
        write_data(temp_config)
        os._exit(0)


class Logger:
    def __init__(self):
        self.red = '\033[91m'
        self.yellow = '\033[93m'
        self.green = '\033[92m'
        self.grey = '\033[90m'
        self.reset = '\033[37m'

    def fetch_time(self, time_type='now'):
        datetime_obj = datetime.now()

        match time_type:
            case 'now':
                time = datetime.now().strftime('%H:%M:%S')
                return f'[{time}]'
            case 'date':
                date = datetime_obj.strftime('%d-%m-%Y')
                return date
            case 'full':
                date = datetime_obj.strftime('%d/%m/%Y')
                time = datetime_obj.strftime('%H:%M:%S')
                return f'[{date} {time}]'
            case _:
                time = datetime.now().strftime('%H:%M:%S')
                return time

    def info(self, text):
        current_time = self.fetch_time()
        print(f'{current_time} {self.grey}[*]{self.reset} {text}')

    def error(self, text):
        current_time = self.fetch_time()
        print(f'{current_time} {self.red}[!]{self.reset} {text}')

    def warning(self, text):
        current_time = self.fetch_time()
        print(f'{current_time} {self.yellow}[!]{self.reset} {text}')


    def success(self, text):
        current_time = self.fetch_time()
        print(f'{current_time} {self.green}[+]{self.reset} {text}')

log = Logger()