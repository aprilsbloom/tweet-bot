from typing import Final
from utils.config import Config, load_cfg, save_cfg

headers: Final = {
	"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
	"Accept": "*/*",
	"Accept-Encoding": "gzip, deflate, br",
	"Connection": "keep-alive",
}

cfg: Config = load_cfg(
  {
    "user_hash": "",
    "queue": [],
    "discord": {
      "token": "",
      "authed_users": [],
      "emojis": {},
			"notifs": {
				"post": {
					"enabled": False,
					"webhook": "",
					"role_to_ping": "",
				},
				"misc": {
					"enabled": False,
					"webhook": "",
					"role_to_ping": "",
				}
			},
      "embed_colors": {
        "success": "#2ECC71",
        "error": "#ff0000",
        "info": "#3498DB",
      },
    },
    "twitter": {
      "enabled": False,
      "consumer_key": "",
      "consumer_secret": "",
      "access_token": "",
      "access_token_secret": "",
    },
    "tumblr": {
      "enabled": False,
      "consumer_key": "",
      "consumer_secret": "",
      "oauth_token": "",
      "oauth_token_secret": "",
    },
    "mastodon": {
      "enabled": False,
      "api_url": "https://botsin.space/",
      "client_id": "",
      "client_secret": "",
      "access_token": "",
    },
		"bluesky": {
			"enabled": False,
			"username": "",
			"app_password": "",
		}
  },
)
save_cfg(cfg)