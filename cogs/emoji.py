import discord
from discord.ext import commands
from utils.config import load_config, write_config

class Emoji(commands.Cog):
	def __init__(self, bot: commands.Bot):
		self.bot = bot

async def setup(bot: commands.Bot):
	await bot.add_cog(Emoji(bot))