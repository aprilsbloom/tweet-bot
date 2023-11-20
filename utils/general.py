import discord
from typing import Optional
from utils.config import load_config

def create_embed(title, description, color):
	config = load_config()
	return discord.Embed(
		title=title,
		description=description,
		color=discord.Color.from_str(config["discord"]["embed_colors"][color])
	)

def is_user_authorized(user_id, bot_info):
	config = load_config()
	return user_id in config["discord"]["authed_users"] or user_id == bot_info.owner.id

async def handleResponse(
	interaction: discord.Interaction,
	config: dict,
	responseType: str,
	content: str,
	image_url: Optional[str] = None,
	ephemeral: bool = False
):
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