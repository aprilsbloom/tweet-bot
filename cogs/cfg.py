import discord
from discord.ext import commands

from globals import cfg, is_authed, is_owner
from utils.config import save_cfg



class Config(commands.Cog):
	def __init__(self, bot: commands.Bot):
		self.bot = bot

	group = discord.app_commands.Group(name = "cfg", description = "Modify config values")

	@group.command(name = "set-emoji", description = "Set your emoji")
	@discord.app_commands.describe(emoji = "The emoji you want to set")
	async def set_emoji(self, interaction: discord.Interaction, emoji: str):
		if not is_authed(interaction):
			await interaction.response.send_message(
				embed = discord.Embed(
					title = "Error",
					description = "You are not authorized to use this command.",
					color = discord.Color.red()
				)
			)

		# make emoji max 10 chars long
		if len(emoji) > 10:
			emoji = emoji[:10]

		cfg["discord"]["emojis"][interaction.user.id] = emoji
		save_cfg(cfg)
		await interaction.response.send_message(
			embed = discord.Embed(
				title = "Success",
				description = f"Set your emoji to {emoji}.",
				color = discord.Color.green()
			)
		)

	@group.command(name = "get-emoji", description = "Get your emoji")
	async def get_emoji(self, interaction: discord.Interaction):
		if not is_authed(interaction):
			await interaction.response.send_message(
				embed = discord.Embed(
					title = "Error",
					description = "You are not authorized to use this command.",
					color = discord.Color.red()
				)
			)

		emoji = cfg["discord"]["emojis"].get(interaction.user.id)
		if emoji is None:
			await interaction.response.send_message(
				embed = discord.Embed(
					title = "Error",
					description = "You don't have an emoji set.",
					color = discord.Color.red()
				)
			)
			return

		await interaction.response.send_message(
			embed = discord.Embed(
				title = "Success",
				description = f"Your emoji is {emoji}.",
				color = discord.Color.green()
			)
		)


	@group.command(name = 'auth', description = 'Authorize a user to use the bot')
	@discord.app_commands.describe(user = 'The user to authorize')
	async def auth_user(self, interaction: discord.Interaction, user: discord.User):
		if not is_owner(self.bot, interaction):
			await interaction.response.send_message(
				embed = discord.Embed(
					title = "Error",
					description = "You are not authorized to use this command.",
					color = discord.Color.red()
				)
			)
			return

		if user.id in cfg["discord"]["authed_users"]:
			await interaction.response.send_message(
				embed = discord.Embed(
					title = "Error",
					description = f"{user.mention} is already authorized.",
					color = discord.Color.red()
				)
			)
			return

		cfg["discord"]["authed_users"].append(user.id)
		save_cfg(cfg)
		await interaction.response.send_message(
			embed = discord.Embed(
				title = "Success",
				description = f"Authorized {user.mention}.",
				color = discord.Color.green()
			)
		)

	@group.command(name = 'deauth', description = 'Deauthorize a user to prevent them using the bot')
	@discord.app_commands.describe(user = 'The user to deauthorize')
	async def deauth_user(self, interaction: discord.Interaction, user: discord.User):
		if not is_owner(self.bot, interaction):
			await interaction.response.send_message(
				embed = discord.Embed(
					title = "Error",
					description = "You are not authorized to use this command."
				)
			)
			return

		if user.id not in cfg["discord"]["authed_users"]:
			await interaction.response.send_message(
				embed = discord.Embed(
					title = "Error",
					description = f"{user.mention} is not authorized.",
					color = discord.Color.red()
				)
			)
			return

		cfg["discord"]["authed_users"].remove(user.id)
		save_cfg(cfg)
		await interaction.response.send_message(
			embed = discord.Embed(
				title = "Success",
				description = f"Deauthorized {user.mention}.",
				color = discord.Color.green()
			)
		)



async def setup(bot: commands.Bot):
	await bot.add_cog(Config(bot))