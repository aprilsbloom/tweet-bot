import discord
from typing import Optional, Union
from utils.config import load_config, write_config
from utils.logger import Logger

log = Logger()

def create_embed(title: str, description: str, color: str):
	config = load_config()
	return discord.Embed(
		title=title,
		description=description,
		color=discord.Color.from_str(config["discord"]["embed_colors"][color])
	)

def is_user_authorized(user_id: Union[int, str], bot_info: discord.AppInfo):
	"""
	Checks if a user is authorized to run commands

	Args
	----
		- user_id (int): The user ID to check
		- bot_info (discord.AppInfo): The bot's application info
	"""

	config = load_config()
	return user_id in config["discord"]["authed_users"] or user_id == bot_info.owner.id

async def error_response(interaction: discord.Interaction, error, command_name):
	config = load_config()
	log.error(f"An error has occurred while running {command_name}\n{error}")
	return await handle_base_response(
		interaction = interaction,
		config = config,
		content = f'An unknown error has occurred:\n```{error}\n```',
		responseType = 'error'
	)

async def handle_base_response(
	interaction: discord.Interaction,
	config: dict,
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
		- config (dict): The config file
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
				config["discord"]["embed_colors"]["success"]
			)
		case "info":
			embed.title = "Info"
			embed.color = discord.Color.from_str(
				config["discord"]["embed_colors"]["info"]
			)
		case "error":
			embed.title = "Error"
			embed.color = discord.Color.from_str(
				config["discord"]["embed_colors"]["error"]
			)

	# set img url if present
	if image_url:
		embed.set_image(url = image_url)

	# respond with the embed
	try:
		if interaction.response.is_done():
			return await interaction.edit_original_response(embed = embed, ephemeral=ephemeral)
		else:
			return await interaction.response.send_message(embed = embed, ephemeral=ephemeral)
	except:
		pass