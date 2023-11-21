import discord
from cogs.queue._views import DeleteConfirmation, EditPostModal
from utils.general import is_user_authorized, create_embed
from utils.config import load_config, write_config

async def delete_response(interaction: discord.Interaction, bot_info: discord.AppInfo, post: dict):
	"""
	Returns the base response to delete a post

	Args
	----
		- interaction (discord.Interaction): The interaction to respond to
		- bot_info (discord.AppInfo): The bot's application info
		- post (dict): The post to delete
	"""

	if not is_user_authorized(interaction.user.id, bot_info):
		return await interaction.response.send_message(
			embed = create_embed(
				"Error",
				"You do not have permission to delete posts.\nPlease ask an administrator for access if you believe this to be in error.",
				'error'
			),
			ephemeral = True
		)

	return await interaction.response.send_message(
		embed = create_embed(
			"Confirmation",
			"Are you sure you want to delete this post?",
			'info'
		),
		view = DeleteConfirmation(post = post, bot_info = bot_info),
		ephemeral = True
	)

async def edit_response(interaction: discord.Interaction, bot_info: discord.AppInfo, post: dict):
	"""
	Returns the modal to edit a post

	Args
	----
		- interaction (discord.Interaction): The interaction to respond to
		- bot_info (discord.AppInfo): The bot's application info
		- post (dict): The post to edit
	"""

	if not is_user_authorized(interaction.user.id, bot_info):
		return await interaction.response.send_message(
			embed = create_embed(
				"Error",
				"You do not have permission to edit posts.\nPlease ask an administrator for access if you believe this to be in error.",
				'error'
			),
			ephemeral = True
		)

	return await interaction.response.send_modal(EditPostModal(post = post))
