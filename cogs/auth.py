import discord
import traceback
from discord.ext import commands
from utils.config import fetch_data, write_data
from utils.general import handleResponse


# Command
class Auth(commands.Cog):
	def __init__(self, bot: commands.Bot):
		self.bot = bot

	group = discord.app_commands.Group(
		name = "auth",
		description = 'Modify a user\'s authentication status'
	)

	@group.command(
		name = 'remove',
		description = 'Remove a given user\'s authentication'
	)
	async def auth_remove(self, interaction: discord.Interaction, user: discord.Member):
		config = fetch_data()
		bot_info = await self.bot.application_info()

		if interaction.user.id != bot_info.owner.id:
			return await handleResponse(
				interaction=interaction,
				config=config,
				content="You do not have permission to run this command.",
				responseType="error",
			)

		if interaction.user.id not in config["discord"]["authed_users"]:
			return await handleResponse(
				interaction=interaction,
				config=config,
				content=f"{user.mention} is currently not authenticated.",
				responseType="error",
			)

		config["discord"]["authed_users"].remove(interaction.user.id)
		write_data(config)

		return await handleResponse(
			interaction=interaction,
			config=config,
			content=f"{user.mention} has had their authentication revoked.",
			responseType="success",
		)

	@auth_remove.error
	async def auth_remove_error(self, interaction: discord.Interaction, error):
		config = fetch_data()
		return await handleResponse(
			interaction = interaction,
			config = config,
			content = f'An unknown error has occurred:\n```\n{traceback.print_exc(error)}\n```',
			responseType = 'error'
		)


	@group.command(
		name = 'add',
		description = 'Authenticate a given user'
	)
	async def auth_add(self, interaction: discord.Interaction, user: discord.Member):
		config = fetch_data()
		bot_info = await self.bot.application_info()

		if interaction.user.id != bot_info.owner.id:
			return await handleResponse(
				interaction=interaction,
				config=config,
				content="You do not have permission to run this command.",
				responseType="error",
			)

		if interaction.user.id in config["discord"]["authed_users"]:
			return await handleResponse(
				interaction=interaction,
				config=config,
				content=f"{user.mention} is already authenticated.",
				responseType="error",
			)

		config["discord"]["authed_users"].append(interaction.user.id)
		write_data(config)
		return await handleResponse(
			interaction=interaction,
			config=config,
			content=f"{user.mention} has been authenticated.",
			responseType="success",
		)

	@auth_add.error
	async def auth_add_error(self, interaction: discord.Interaction, error):
		config = fetch_data()
		return await handleResponse(
			interaction = interaction,
			config = config,
			content = f'An unknown error has occurred:\n```\n{traceback.print_exc(error)}\n```',
			responseType = 'error'
		)

# Cog setup
async def setup(bot: commands.Bot):
	await bot.add_cog(Auth(bot))
