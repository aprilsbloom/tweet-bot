import discord
from discord.ext import commands

group = discord.app_commands.Group(
	name = "emoji",
	description = "Modify or view your emoji status"
)

class Emoji(commands.Cog):
	def __init__(self, bot: commands.Bot):
		self.bot = bot

async def setup(bot: commands.Bot):
	await bot.add_cog(Emoji(bot))