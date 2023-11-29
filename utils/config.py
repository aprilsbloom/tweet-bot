import json
import os
from pathlib import Path
from typing import Union, Final, Optional

DEFAULT_CFG: Final = {
	"userhash": "enter a randomly generated string here",
	"discord": {
		"token": "",
		"authed_users": [],
		"emojis": {},
		"embed_colors": {
			"success": "#2ECC71",
			"error": "#ff0000",
			"info": "#3498DB",
		},
	},
	"twitter": {
		"consumer_key": "",
		"consumer_secret": "",
		"access_token": "",
		"access_token_secret": "",
		"queue": [],
	}
}

def merge_objects(obj1, obj2):
	# create new object that we merge to
	merged_object = {}

	# iterate over the first objects keys
	for key in obj2.keys():
		# if key is in second object, and it's another object, merge them recursively
		if key in obj1 and isinstance(obj2[key], dict) and isinstance(obj1[key], dict):
			merged_object[key] = merge_objects(obj1[key], obj2[key])

		# if key is not in second object, or it's not a object/list, add it to the merged object
		else:
			merged_object[key] = obj2[key]

	# iterate over the second objects keys
	for key in obj1.keys():
		# If the key is not already in the merged object, add it
		if key not in merged_object:
			merged_object[key] = obj1[key]

	return merged_object

def load_config(path: Union[str, os.PathLike, Path] = 'config.json') -> dict:
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

	# if path isn't a path object, make it one
	if not isinstance(path, Path):
		path = Path(path)

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
	config = merge_objects(DEFAULT_CFG, config)

	# write config file to disk
	write_config(config, path)

	# return the config file
	return config

def write_config(data: dict, path: Union[str, os.PathLike, Path] = 'config.json', format: Optional[str] = 'pretty', sort_keys: Optional[bool] = False) -> None:
	"""
	Writes the given data to the specified path as a json file

	Args
	----
	- data: dict
		- The data to write to the file
	- path: Union[str, os.PathLike, Path]
		- The path to write the file to
	- format: Optional[str]
		- The format to write the file in, either 'pretty' or 'compact'
	- sort_keys: Optional[bool]
		- Whether or not to sort the keys in the file
	"""

	# set the indent level and separators based on the format provided
	indent_level = 4 if format == 'pretty' else None
	separators = None if format == 'pretty' else (',', ':')

	# if path isn't a path object, make it one
	if not isinstance(path, Path):
		path = Path(path)

	# if the path doesn't exist, create it
	if not path.exists():
		path.touch()

	# write the config file
	with open(path, 'w', encoding='utf8') as f:
		f.write(json.dumps(data, indent=indent_level, separators=separators, sort_keys=sort_keys))