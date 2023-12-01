import traceback
import discord
from typing import Optional, Union
from utils.globals import cfg, log

def remove_post(post):
	"""
	Removes a post from the queue

	Args
	----
		- post (dict): The post to remove
	"""

	queue = cfg.get('queue')
	queue.remove(post)
	cfg.set('queue', queue)


def edit_post(post, args):
	"""
	Edits a post in the queue

	Args
	----
		- post (dict): The post to edit
		- args (dict): The arguments to edit the post with
			- caption (str): The caption to set on the post
			- alt_text (str): The alt text to set on the post
	"""

	queue = cfg.get('queue')
	have_found_post = False
	found_post = None
	for tmpPost in queue:
		if tmpPost["catbox_url"] == post['catbox_url']:
			have_found_post = True
			found_post = tmpPost
			break

	if have_found_post:
		post_index = queue.index(found_post)

		if args.get('caption', '') == '':
			del queue[post_index]['caption']
		else:
			queue[post_index]["caption"] = args.get('caption', '')

		queue[post_index]["alt_text"] = args.get('alt_text', '')
		cfg.set('queue', queue)


def create_embed(title: str, description: str, color: str):
	"""
	Creates an incredibly basic embed for use in responses

	Args
	----
		- title (str): The title of the embed
		- description (str): The description of the embed
		- color (str): The color of the embed
			- Either `success`, `info`, or `error`
	"""

	return discord.Embed(
		title=title,
		description=description,
		color=discord.Color.from_str(cfg.get(f'discord.embed_colors.{color}'))
	)


def is_user_authorized(user_id: Union[int, str], bot_info: discord.AppInfo):
	"""
	Checks if a user is authorized to run commands

	Args
	----
		- user_id (int): The user ID to check
		- bot_info (discord.AppInfo): The bot's application info
	"""

	return int(user_id) in cfg.get('discord.authed_users') or user_id == bot_info.owner.id


async def error_response(interaction: discord.Interaction, error, command_name):
	"""
	Creates an incredibly basic error response for use in @command.error decorators


	"""

	log.error(f"An error has occurred while running {command_name}\n{error}")
	return await handle_base_response(
		interaction = interaction,
		responseType = 'error',
		content = f'An unknown error has occurred:\n```{error}\n```',
	)


# TODO: remove this in favor of making everything ourself
# no need for this tbh it's just bloat and really terribly wrote lmao
async def handle_base_response(
	interaction: discord.Interaction,
	responseType: str,
	content: str,
	image_url: Optional[str] = None,
	ephemeral: Optional[bool] = False
):
	"""
	Handles sending a response to an interaction

	Args
	----
		- interaction (discord.Interaction): The interaction to respond to
		- responseType (str): The type of response to send
		- content (str): The content of the response, which will be set as the embed description
		- image_url (Optional[str]): The image URL to set on the embed
		- ephemeral (Optional[bool]): Whether or not the response should be ephemeral
	"""
	embed = discord.Embed(description = content)

	# embed title and color
	match responseType:
		case "success":
			embed.title = "Success"
			embed.color = discord.Color.from_str(
				cfg.get('discord.embed_colors.success')
			)
		case "info":
			embed.title = "Info"
			embed.color = discord.Color.from_str(
				cfg.get('discord.embed_colors.info')
			)
		case "error":
			embed.title = "Error"
			embed.color = discord.Color.from_str(
				cfg.get('discord.embed_colors.error')
			)

	# set img url if present
	if image_url:
		embed.set_image(url = image_url)

	# respond with the embed
	try:
		if interaction.response.is_done():
			return await interaction.edit_original_response(embed = embed)
		else:
			return await interaction.response.send_message(embed = embed, ephemeral=ephemeral)
	except Exception as e:
		print(traceback.format_exc())