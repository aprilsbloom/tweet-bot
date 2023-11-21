import discord
from discord.ext import commands



class Emoji(commands.Cog):
	def __init__(self, bot: commands.Bot):
		self.bot = bot

	group = discord.app_commands.Group(
		name = "emoji",
		description = "Modify or view your emoji status"
	)

async def setup(bot: commands.Bot):
	await bot.add_cog(Emoji(bot))