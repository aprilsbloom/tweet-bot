import discord
from discord.ext import commands
from utils.general import create_embed, error_response, handle_base_response, is_user_authorized
from utils.globals import cfg



class Emoji(commands.Cog):
	def __init__(self, bot: commands.Bot):
		self.bot = bot

	group = discord.app_commands.Group(name = "emoji", description = "Modify or view your emoji status")

	@group.command(name = "set", description = "Set your emoji")
	@discord.app_commands.describe(emoji = "The emoji you want to set")
	async def set_emoji(self, interaction: discord.Interaction, emoji: str):
		bot_info = await self.bot.application_info()

		# Check if the user is authorized to run this command
		if not is_user_authorized(interaction.user.id, bot_info):
			return await interaction.response.send_message(
				embed = create_embed(
					"Error",
					"You do not have permission to run this command.\nPlease ask an administrator for access if you believe this to be in error.",
					'error'
				),
				ephemeral = True
			)

		cfg.set(f'discord.emojis.{interaction.user.id}', emoji)

		return await handle_base_response(
			interaction = interaction,
			responseType = "success",
			content = f"Your emoji has been set to {emoji}",
		)

	@set_emoji.error
	async def set_emoji(self, interaction: discord.Interaction, error):
		await error_response(interaction, error, '/emoji set')


	@group.command(name = "remove", description = "Remove your emoji from the list")
	async def remove_emoji(self, interaction: discord.Interaction):
		bot_info = await self.bot.application_info()

		# Check if the user is authorized to run this command
		if not is_user_authorized(interaction.user.id, bot_info):
			return await interaction.response.send_message(
				embed = create_embed(
					"Error",
					"You do not have permission to run this command.\nPlease ask an administrator for access if you believe this to be in error.",
					'error'
				),
				ephemeral = True
			)


		# If the user doesn't have an emoji, return an error
		emojis = cfg.get('discord.emojis')
		if str(interaction.user.id) not in emojis:
			return await handle_base_response(
				interaction = interaction,
				responseType = "error",
				content = "You do not have an emoji set.",
			)

		del emojis[str(interaction.user.id)]
		cfg.set('discord.emojis', emojis)

		return await handle_base_response(
			interaction = interaction,
			responseType = "success",
			content = "Your emoji has been removed.",
		)

	@remove_emoji.error
	async def remove_emoji(self, interaction: discord.Interaction, error):
		await error_response(interaction, error, '/emoji remove')


	@group.command(name = "view", description = "View the emoji you have set")
	async def view_emoji(self, interaction: discord.Interaction):
		bot_info = await self.bot.application_info()

		# Check if the user is authorized to run this command
		if not is_user_authorized(interaction.user.id, bot_info):
			return await interaction.response.send_message(
				embed = create_embed(
					"Error",
					"You do not have permission to run this command.\nPlease ask an administrator for access if you believe this to be in error.",
					'error'
				),
				ephemeral = True
			)


		# If the user doesn't have an emoji, return an error
		emojis = cfg.get('discord.emojis')
		if str(interaction.user.id) not in emojis:
			return await handle_base_response(
				interaction = interaction,
				responseType = "error",
				content = "You do not have an emoji set.",
			)


		# Return the users emoji
		return await handle_base_response(
			interaction = interaction,
			responseType = "info",
			content = f"Your emoji is: {emojis[str(interaction.user.id)]}",
		)

	@view_emoji.error
	async def view_emoji(self, interaction: discord.Interaction, error):
		await error_response(interaction, error, '/emoji view')


	@group.command(name = "list", description = "List all emojis that have been set by other users")
	async def list_emoji(self, interaction: discord.Interaction):
		bot_info = await self.bot.application_info()

		# Check if the user is authorized to run this command
		if not is_user_authorized(interaction.user.id, bot_info):
			return await interaction.response.send_message(
				embed = create_embed(
					"Error",
					"You do not have permission to run this command.\nPlease ask an administrator for access if you believe this to be in error.",
					'error'
				),
				ephemeral = True
			)


		# If there are no emojis, return an error
		emojis = cfg.get('discord.emojis')
		if len(emojis) == 0:
			return await handle_base_response(
				interaction = interaction,
				responseType = "error",
				content = "No users have set an emoji yet.",
			)


		return await interaction.response.send_message(
			embed = create_embed(
				"Emoji list",
				"\n".join([f"<@{user}> - {emoji}" for user, emoji in emojis.items()]),
				"info"
			)
		)

	@list_emoji.error
	async def list_emoji(self, interaction: discord.Interaction, error):
		await error_response(interaction, error, '/emoji list')


async def setup(bot: commands.Bot):
	await bot.add_cog(Emoji(bot))