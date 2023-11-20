import discord
import os
import traceback
from pathlib import Path
from typing import Union
from discord.ext import commands, tasks
from utils.config import load_config, write_config
from utils.logger import Logger

log = Logger()
config = load_config()

class Bot(commands.Bot):
	def __init__(self):
		super().__init__(intents = discord.Intents.default(), command_prefix='')

	async def setup_hook(self):
		await self.setupCommands("cogs")

		try:
			synced = await bot.tree.sync()
			log.info(f"Synced {len(synced)} commands")
		except Exception:
			log.error(f"An error has occurred while syncing commands.\n{traceback.format_exc()}")
			return

	async def setupCommands(self, directory: Union[str, os.PathLike, Path] = "cogs"):
		"""
		Recursively loads all cogs in the specified directory.

		Args
		----
		- directory: Union[str, os.PathLike, Path]
			- The directory to load cogs from (default: "cogs")
		"""
		for root, dirs, files in os.walk(directory):
			for file in files:
				if file.endswith(".py") and not file.startswith("_"):
					cog_path = (os.path.join(root, file).replace(os.sep, ".").rstrip(".py"))

					try:
						await self.load_extension(cog_path)
					except (commands.errors.ExtensionAlreadyLoaded):
						pass
					except:
						log.error(f'Unable to load {cog_path}\n{traceback.format_exc()}')
			for dir in dirs:
				await self.setupCommands(os.path.join(root, dir))

	async def on_ready(self):
		await self.wait_until_ready()
		log.success(f"Logged in as {self.user}.")

bot = Bot()
bot.run(config['discord']['token'])