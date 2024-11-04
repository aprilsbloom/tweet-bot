import json
import dataconf
from dataclasses import dataclass
from typing import List, Dict, Optional

def deep_merge(obj1, obj2):
	# create new object that we merge to
	merged_object = {}

	# iterate over the first objects keys
	for key in obj2.keys():
		# if key is in first object, and it's in second object, merge them recursively
		if key in obj1 and isinstance(obj1[key], dict) and isinstance(obj2[key], dict):
			merged_object[key] = deep_merge(obj1[key], obj2[key])

		# if key is not in second object, or it's not a object/list, add it to the merged object
		else:
			merged_object[key] = obj2[key]

	# iterate over the second objects keys
	for key in obj1.keys():
		# If the key is not already in the merged object, add it
		if key not in merged_object:
			merged_object[key] = obj1[key]

	return merged_object

@dataclass
class Post():
	author_id: int
	alt_text: str
	caption: Optional[str]
	catbox_url: str
	raw_url: str

@dataclass
class DiscordNotification():
	enabled: bool
	webhook: str
	role_to_ping: Optional[int]

@dataclass
class DiscordConfig():
	token: str
	authed_users: List[int]
	emojis: Dict[int, str]
	embed_colors: Dict[str, str]
	notifs: Dict[str, DiscordNotification]

@dataclass
class TwitterConfig():
	enabled: bool
	consumer_key: str
	consumer_secret: str
	access_token: str
	access_token_secret: str

@dataclass
class TumblrConfig():
	enabled: bool
	consumer_key: str
	consumer_secret: str
	oauth_token: str
	oauth_token_secret: str

@dataclass
class MastodonConfig():
	enabled: bool
	api_url: str
	client_id: str
	client_secret: str
	access_token: str

@dataclass
class BlueskyConfig():
	enabled: bool
	username: str
	app_password: str

@dataclass
class Config():
	user_hash: str
	queue: List[Post]
	discord: DiscordConfig
	twitter: TwitterConfig
	tumblr: TumblrConfig
	mastodon: MastodonConfig
	bluesky: BlueskyConfig

	@staticmethod
	def load(default: dict = {}):
		try:
			with open("config.json", 'r', encoding='utf8') as f:
				config = json.loads(f.read())
		except (json.JSONDecodeError, FileNotFoundError):
			config = default

		merged = deep_merge(default, config)
		return dataconf.dict(merged, Config)

	def save(self):
		with open('config.json', 'w', encoding='utf8') as f:
			f.write(json.dumps(self.__dict__))