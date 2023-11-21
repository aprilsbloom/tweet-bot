import discord
from discord.ext import commands
from utils.general import handle_base_response, error_response
from utils.config import load_config, write_config



class Auth(commands.Cog):
	def __init__(self, bot: commands.Bot):
		self.bot = bot

	group = discord.app_commands.Group(
		name = "auth",
		description = "Modify a user's authentication status"
	)

	@group.command(
		name = 'remove',
		description = "Remove a given user's authentication"
	)
	async def auth_remove(self, interaction: discord.Interaction, user: discord.Member):
		config = load_config()
		bot_info = await self.bot.application_info()

		# only let bot owner run command
		if interaction.user.id != bot_info.owner.id:
			return await handle_base_response(
				interaction=interaction,
				config=config,
				content="You do not have permission to run this command.",
				responseType="error",
			)

		# if the user isn't in the list of authed users, return an error
		if interaction.user.id not in config["discord"]["authed_users"]:
			return await handle_base_response(
				interaction=interaction,
				config=config,
				content=f"{user.mention} is currently not authenticated.",
				responseType="error",
			)

		# remove the user from the list of authed users
		config["discord"]["authed_users"].remove(interaction.user.id)
		write_config(config)

		return await handle_base_response(
			interaction=interaction,
			config=config,
			content=f"{user.mention} has had their authentication revoked.",
			responseType="success",
		)

	@auth_remove.error
	async def auth_remove_error(self, interaction: discord.Interaction, error):
		return await error_response(interaction, error, '/auth remove')

	@group.command(
		name = 'add',
		description = 'Authenticate a given user'
	)
	async def auth_add(self, interaction: discord.Interaction, user: discord.Member):
		config = load_config()
		bot_info = await self.bot.application_info()

		# only let bot owner run command
		if interaction.user.id != bot_info.owner.id:
			return await handle_base_response(
				interaction=interaction,
				config=config,
				content="You do not have permission to run this command.",
				responseType="error",
			)

		# if the user is already in the list of authed users, return an error
		if interaction.user.id in config["discord"]["authed_users"]:
			return await handle_base_response(
				interaction=interaction,
				config=config,
				content=f"{user.mention} is already authenticated.",
				responseType="error",
			)

		# add the user to the list of authed users
		config["discord"]["authed_users"].append(interaction.user.id)
		write_config(config)

		return await handle_base_response(
			interaction=interaction,
			config=config,
			content=f"{user.mention} has been authenticated.",
			responseType="success",
		)

	@auth_add.error
	async def auth_add_error(self, interaction: discord.Interaction, error):
		return await error_response(interaction, error, '/auth add')

async def setup(bot: commands.Bot):
	await bot.add_cog(Auth(bot))