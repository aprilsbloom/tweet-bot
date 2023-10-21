import discord
from discord.ext import commands
from utils.config import fetch_data, write_data
from utils.general import handleResponse
from typing import Optional

# Command
class Emoji(commands.Cog):
	def __init__(self, bot: commands.Bot):
		self.bot = bot

	@discord.app_commands.command(name = 'emoji', description = 'Add / remove authentication for a given user')
	@discord.app_commands.describe(
		cmd_choice = 'The command you want to run',
		emoji = 'The emoji you want to add/remove (optional)'
	)
	@discord.app_commands.choices(cmd_choice = [
		discord.app_commands.Choice(name = 'Set', value = 'set'),
		discord.app_commands.Choice(name = 'Remove', value = 'remove'),
		discord.app_commands.Choice(name = 'View', value = 'view'),
		discord.app_commands.Choice(name = 'View all', value = 'view_all'),
	])
	async def emoji(self, interaction: discord.Interaction, cmd_choice: discord.app_commands.Choice[str], emoji: Optional[str] = ''):
		config = fetch_data()
		bot_info = await self.bot.application_info()
		owner_id = bot_info.owner.id

		if interaction.user.id not in config['discord']['authed_users'] and interaction.user.id != owner_id:
			return await handleResponse(
				interaction = interaction,
				config = config,
				content = 'You do not have permission to run this command.\nPlease ask an administrator for access if you believe this to be in error.',
				responseType = 'error'
			)

		if cmd_choice.value == 'set':
			if emoji == '':
				return await handleResponse(
					interaction = interaction,
					config = config,
					content = 'You have not set an emoji.',
					responseType = 'error',
				)
			else:
				config['discord']['emojis'][str(interaction.user.id)] = emoji
				write_data(config)

				return await handleResponse(
					interaction = interaction,
					config = config,
					content = f'Your emoji has been set to {emoji}',
					responseType = 'success'
				)
		elif cmd_choice.value == 'remove':
			if str(interaction.user.id) not in config['discord']['emojis'].keys():
				return await handleResponse(
					interaction = interaction,
					config = config,
					content = 'You do not have an emoji set.',
					responseType = 'error'
				)
			else:
				del config['discord']['emojis'][str(interaction.user.id)]
				write_data(config)

				return await handleResponse(
					interaction = interaction,
					config = config,
					content = 'Your emoji has been successfully removed',
					responseType = 'success'
				)
		elif cmd_choice.value == 'view':
			if str(interaction.user.id) not in config['discord']['emojis'].keys():
				return await handleResponse(
					interaction = interaction,
					config = config,
					content = 'You do not have an emoji set.',
					responseType = 'error'
				)
			else:
				user_emoji = config['discord']['emojis'][str(interaction.user.id)]
				return await handleResponse(
					interaction = interaction,
					config = config,
					content = f'**Your emoji:** {user_emoji}',
					responseType = 'info'
				)
		elif cmd_choice.value == 'view_all':
			emojis = config['discord']['emojis']
			content = ''

			if len(emojis.keys()) == 0:
				return await handleResponse(
					interaction = interaction,
					config = config,
					content = 'No emojis have been set.\nPlease use /emoji set to set your own emoji.',
					responseType = 'error'
				)

			for user in emojis:
				content += f'**<@{user}>** - {emojis[user]}\n'

			return await handleResponse(
				interaction = interaction,
				config = config,
				content = content,
				responseType = 'info'
			)

	@emoji.error
	async def emoji_error(self, interaction: discord.Interaction, error):
		config = fetch_data()
		return await handleResponse(
			interaction = interaction,
			config = config,
			content = f'An unknown error has occurred:\n```\n{error}\n```',
			responseType = 'error'
		)

# Cog setup
async def setup(bot: commands.Bot):
	await bot.add_cog(Emoji(bot))