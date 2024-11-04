from utils.config import Config

cfg: Config = Config.load(
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
					"webhook": ""
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
cfg.save() # type: ignore

print(type(cfg))