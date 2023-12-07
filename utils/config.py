import json
import os
from pathlib import Path
from typing import Union, Final, Optional

# Default configuration file
DEFAULT_CFG: Final = {
	"userhash": "enter a randomly generated string here",
	"queue": [],
	"discord": {
		"token": "",
		"post_notifs": {
			"enabled": True,
			"webhook": "",
			"role_to_ping": ""
		},
		"misc_notifs": {
			"enabled": True,
			"webhook": ""
		},
		"authed_users": [],
		"emojis": {},
		"embed_colors": {
			"success": "#2ECC71",
			"error": "#ff0000",
			"info": "#3498DB"
		}
	},
	"twitter": {
		"enabled": True,
		"consumer_key": "",
		"consumer_secret": "",
		"access_token": "",
		"access_token_secret": ""
	},
	"tumblr": {
		"enabled": True,
		"consumer_key": "",
		"consumer_secret": "",
		"oauth_token": "",
		"oauth_secret": ""
	},
	"mastodon": {
		"enabled": True,
		"api_url": "",
		"client_id": "",
		"client_secret": "",
		"access_token": ""
	}
}


class Config():
	def __init__(self, path: Union[str, os.PathLike, Path]) -> None:
		self.cfg_path: Path = Path(path)
		self.config: dict = self.load_config(path)

	def load_config(self, path: Union[str, os.PathLike, Path]) -> dict:
		"""
		Loads the config file from the specified path

		Args
		----
		- path: Union[str, os.PathLike, Path]
			- The path to the config file

		Returns
		----
		- dict
			- The loaded config file
		"""

		path = self.cfg_path

		# if the path doesn't exist, create it
		if not path.exists():
			path.touch()

		# load the config file
		try:
			with open(path, 'r', encoding='utf8') as f:
				config = json.loads(f.read())
		except json.JSONDecodeError:
			config = DEFAULT_CFG

		# merge newly loaded config file with default config
		self.config = deep_merge(DEFAULT_CFG, config)

		# write config file to disk
		self.write_config()

		# return the config file
		return self.config

	def write_config(self, format: Optional[str] = 'pretty', sort_keys: Optional[bool] = False) -> None:
		"""
		Writes the given data to the specified path as a json file

		Args
		----
		- format: Optional[str]
			- The format to write the file in, either 'pretty' or 'compact'
		- sort_keys: Optional[bool]
			- Whether or not to sort the keys in the file
		"""

		# set the indent level and separators based on the format provided
		indent_level = 4 if format == 'pretty' else None
		separators = None if format == 'pretty' else (',', ':')

		path = self.cfg_path

		# if the path doesn't exist, create it
		if not path.exists():
			path.touch()

		# write the config file
		with open(path, 'w', encoding='utf8') as f:
			f.write(json.dumps(self.config, indent=indent_level, separators=separators, sort_keys=sort_keys))

	def getter(self, key, obj = None):
		keys = key.split('.')

		if not obj or not isinstance(obj, dict):
			return None

		if len(keys) == 1:
			return obj.get(key)

		new_key = keys[1:]
		return self.getter('.'.join(new_key), obj.get(keys[0]))

	def setter(self, key, value, obj):
		keys = key.split('.')

		if len(keys) == 1:
			obj[key] = value
			return obj
		else:
			newKey = keys[0]
			obj[newKey] = self.setter('.'.join(keys[1:]), value, obj.get(newKey))

			return obj

	def get(self, key):
		self.config = deep_merge(DEFAULT_CFG, self.config)
		self.write_config()
		return self.getter(key, self.config)

	def set(self, key, value):
		self.config = deep_merge(DEFAULT_CFG, self.config)
		self.config = self.setter(key, value, self.config)
		self.write_config()


def deep_merge(self, obj1, obj2):
	# create new object that we merge to
	merged_object = {}

	# iterate over the first objects keys
	for key in obj2.keys():
		# if key is in second object, and it's another object, merge them recursively
		if key in obj1 and isinstance(obj2[key], dict) and isinstance(obj1[key], dict):
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