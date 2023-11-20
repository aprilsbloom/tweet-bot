import discord
import traceback
from discord.ext import commands
from utils.logger import Logger
from utils.general import handleResponse
from utils.config import load_config, write_config

log = Logger()

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
		config = load_config()
		bot_info = await self.bot.application_info()

		# only let bot owner run command
		if interaction.user.id != bot_info.owner.id:
			return await handleResponse(
				interaction=interaction,
				config=config,
				content="You do not have permission to run this command.",
				responseType="error",
			)

		# if the user isn't in the list of authed users, return an error
		if interaction.user.id not in config["discord"]["authed_users"]:
			return await handleResponse(
				interaction=interaction,
				config=config,
				content=f"{user.mention} is currently not authenticated.",
				responseType="error",
			)

		# remove the user from the list of authed users
		config["discord"]["authed_users"].remove(interaction.user.id)
		write_config(config)

		return await handleResponse(
			interaction=interaction,
			config=config,
			content=f"{user.mention} has had their authentication revoked.",
			responseType="success",
		)

	@auth_remove.error
	async def auth_remove_error(self, interaction: discord.Interaction, error):
		config = load_config()
		return await handleResponse(
			interaction = interaction,
			config = config,
			content = f'An unknown error has occurred:\n```{error}\n```',
			responseType = 'error'
		)


	@group.command(
		name = 'add',
		description = 'Authenticate a given user'
	)
	async def auth_add(self, interaction: discord.Interaction, user: discord.Member):
		config = load_config()
		bot_info = await self.bot.application_info()

		# only let bot owner run command
		if interaction.user.id != bot_info.owner.id:
			return await handleResponse(
				interaction=interaction,
				config=config,
				content="You do not have permission to run this command.",
				responseType="error",
			)

		# if the user is already in the list of authed users, return an error
		if interaction.user.id in config["discord"]["authed_users"]:
			return await handleResponse(
				interaction=interaction,
				config=config,
				content=f"{user.mention} is already authenticated.",
				responseType="error",
			)

		# add the user to the list of authed users
		config["discord"]["authed_users"].append(interaction.user.id)
		write_config(config)

		return await handleResponse(
			interaction=interaction,
			config=config,
			content=f"{user.mention} has been authenticated.",
			responseType="success",
		)

	@auth_add.error
	async def auth_add_error(self, interaction: discord.Interaction, error):
		config = load_config()
		log.error(f"An error has occurred while running /auth add{error}")
		return await handleResponse(
			interaction = interaction,
			config = config,
			content = f'An unknown error has occurred:\n```{error}```',
			responseType = 'error'
		)

async def setup(bot: commands.Bot):
	await bot.add_cog(Auth(bot))