import os
import discord
import traceback
from discord.ext import commands
from utils.config import fetch_data
from utils.logger import log

class Bot(commands.Bot):
	def __init__(self):
		super().__init__(
			intents = discord.Intents.default(),
			command_prefix=''
		)

	async def setup_hook(self):
		await self.setupCommands('cogs')

		try:
			synced = await bot.tree.sync()
			log.info(f'Synced {len(synced)} commands')
		except Exception:
			log.error(f'An error has occurred while syncing commands.\n{traceback.format_exc()}')
			return

	async def setupCommands(self, directory):
		for root, dirs, files in os.walk(directory):
			for file in files:
				if file.endswith('.py'):
					cog_path = os.path.join(root, file).replace(os.sep, '.').rstrip('.py')
					await self.load_extension(cog_path)
			for dir in dirs:
				await self.setupCommands(os.path.join(root, dir))

	async def on_ready(self):
		await self.wait_until_ready()
		print(f'Logged in as {self.user}.')

config = fetch_data()
bot = Bot()
bot.run("OTgwNzQ2OTA5MjIyMzM4NTgw.G3rU21.hp8XspJcDC0yKm5etVPjqTHgpbxiVbuZAwkjCQ")