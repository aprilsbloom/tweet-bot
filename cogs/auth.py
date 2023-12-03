import discord
from discord.ext import commands
from utils.general import handle_base_response, error_response
from utils.globals import cfg


class Auth(commands.Cog):
	def __init__(self, bot: commands.Bot):
		self.bot = bot

	group = discord.app_commands.Group(name = "auth", description = "Modify a user's authentication status")

	@group.command(name = 'remove', description = "Remove a given user's authentication")
	async def auth_remove(self, interaction: discord.Interaction, user: discord.Member):
		bot_info = await self.bot.application_info()

		# only let bot owner run command
		if interaction.user.id != bot_info.owner.id:
			return await handle_base_response(
				interaction=interaction,
				content="You do not have permission to run this command.",
				responseType="error",
			)


		# if the user isn't in the list of authed users, return an error
		authed_users = cfg.get('discord.authed_users')
		if str(interaction.user.id) not in authed_users:
			return await handle_base_response(
				interaction=interaction,
				content=f"{user.mention} is currently not authenticated.",
				responseType="error",
			)


		# remove the user from the list of authed users
		authed_users.remove(str(interaction.user.id))
		cfg.set('discord.authed_users', authed_users)

		return await handle_base_response(
			interaction=interaction,
			content=f"{user.mention} has had their authentication revoked.",
			responseType="success",
		)

	@auth_remove.error
	async def auth_remove_error(self, interaction: discord.Interaction, error):
		return await error_response(interaction, error, '/auth remove')


	@group.command(name = 'add', description = 'Authenticate a given user')
	async def auth_add(self, interaction: discord.Interaction, user: discord.Member):
		bot_info = await self.bot.application_info()

		# only let bot owner run command
		if interaction.user.id != bot_info.owner.id:
			return await handle_base_response(
				interaction=interaction,
				content="You do not have permission to run this command.",
				responseType="error",
			)


		# if the user is already in the list of authed users, return an error
		authed_users = cfg.get('discord.authed_users')
		if str(interaction.user.id) in authed_users:
			return await handle_base_response(
				interaction=interaction,
				content=f"{user.mention} is already authenticated.",
				responseType="error",
			)


		# add the user to the list of authed users
		authed_users.append(str(interaction.user.id))
		cfg.set('discord.authed_users', authed_users)

		return await handle_base_response(
			interaction=interaction,
			content=f"{user.mention} has been authenticated.",
			responseType="success",
		)

	@auth_add.error
	async def auth_add_error(self, interaction: discord.Interaction, error):
		return await error_response(interaction, error, '/auth add')

async def setup(bot: commands.Bot):
	await bot.add_cog(Auth(bot))