import os
import json
from .logger import log

def write_data(data):
    with open('config.json', 'w', encoding='utf8') as file:
        file.write(json.dumps(data, indent=4))

def fetch_data():
    temp_config = {
        "discord": {
            "token": "",
            "archive_channel_id": 0,
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
            "bearer_token": "",
            "post_queue": []
        }
    }

    try:
        with open('config.json', 'r', encoding='utf8') as file:
            temp_config.update(json.loads(file.read()))
            write_data(temp_config)
            return temp_config
    except (FileNotFoundError, json.decoder.JSONDecodeError):
        log.info('Config file not found! Creating one')
        write_data(temp_config)
        os._exit(0)