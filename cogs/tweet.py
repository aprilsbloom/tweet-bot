import discord
from discord.ext import commands
from utils.config import load_config, write_config

class Tweet(commands.Cog):
	def __init__(self, bot: commands.Bot):
		self.bot = bot

async def setup(bot: commands.Bot):
	await bot.add_cog(Tweet(bot))