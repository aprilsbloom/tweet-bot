import discord
from discord.ext import commands
from utils.config import fetch_data, write_data
from utils.general import handleResponse

# Command
class Auth(commands.Cog):
	def __init__(self, bot: commands.Bot):
		self.bot = bot

	@discord.app_commands.command(name = 'auth', description = 'Add / remove authentication for a given user')
	@discord.app_commands.describe(user = 'The user that you wish to add / remove authentication for')
	@discord.app_commands.choices(cmd_choice = [
		discord.app_commands.Choice(name = 'Add', value = 'add'),
		discord.app_commands.Choice(name = 'Remove', value = 'remove'),
	])
	async def auth(self, interaction: discord.Interaction, cmd_choice: discord.app_commands.Choice[str], user: discord.Member):
		config = fetch_data()
		bot_info = await self.bot.application_info()

		if interaction.user.id != bot_info.owner.id:
			return await handleResponse(
				interaction = interaction,
				config = config,
				content = 'You do not have permission to run this command.',
				responseType = 'error'
			)

		if cmd_choice.value == 'add':
			if interaction.user.id in config['discord']['authed_users']:
				return await handleResponse(
					interaction = interaction,
					config = config,
					content = f'{user.mention} is already authenticated.',
					responseType = 'error',
				)
			else:
				config['discord']['authed_users'].append(interaction.user.id)
				write_data(config)
				return await handleResponse(
					interaction = interaction,
					config = config,
					content = f'{user.mention} has been authenticated.',
					responseType = 'success'
				)
		elif cmd_choice.value == 'remove':
			if interaction.user.id not in config['discord']['authed_users']:
				return await handleResponse(
					interaction = interaction,
					config = config,
					content = f'{user.mention} is currently not authenticated.',
					responseType = 'error'
				)
			else:
				config['discord']['authed_users'].remove(interaction.user.id)
				write_data(config)

				return await handleResponse(
					interaction = interaction,
					config = config,
					content = f'{user.mention} has been removed from accessing the bot.',
					responseType = 'success'
				)

	@auth.error
	async def auth_error(self, interaction: discord.Interaction, error):
		config = fetch_data()
		return await handleResponse(
			interaction = interaction,
			config = config,
			content = f'An unknown error has occurred:\n```\n{error}\n```',
			responseType = 'error'
		)


# Cog setup
async def setup(bot: commands.Bot):
	await bot.add_cog(Auth(bot))