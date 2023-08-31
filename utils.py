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
            "archive_channel_id": 1,
            "authed_users": [],
            "emojis": {},
            "embed_colors": {
                "success": "#2ECC71",
                "error": "#ff0000",
                "info": "#3498DB",
            }
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

    def fetch_time(self):
        time = datetime.now().strftime('%H:%M:%S')
        return f'[{time}]'

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