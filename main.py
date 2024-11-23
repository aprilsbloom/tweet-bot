import os
import traceback
from pathlib import Path
from typing import Union

import discord
from discord.ext import commands

from globals import cfg


class Bot(commands.Bot):
	def __init__(self):
		super().__init__(intents=discord.Intents.none(), command_prefix="")

	async def setup_hook(self):
		# fetch bot owner id
		app_info = await self.application_info()
		self.owner_id = app_info.owner.id

		# sync commands
		await self.setupCommands("cogs")

		try:
			synced = await bot.tree.sync()
			print(f"Synced {len(synced)} commands")
		except Exception:
			print(f"An error has occurred while syncing commands.\n{traceback.format_exc()}")

	async def setupCommands(self, directory: Union[str, os.PathLike, Path] = "cogs"):
		for root, _, files in os.walk(directory):
			for file in files:
				if not (file.endswith(".py") or file.startswith("_")):
					continue

				cog_path = os.path.join(root, file).replace(os.sep, ".").rstrip(".py")

				try:
					await self.load_extension(cog_path)
				except commands.errors.ExtensionAlreadyLoaded:
					pass
				except Exception:
					print(f"Unable to load {cog_path}\n{traceback.format_exc()}")

	async def on_ready(self):
		await self.wait_until_ready()
		print(f"Logged in as {self.user}.")

		# current_time = datetime.now()
		# goal_timestamp = current_time + timedelta(hours = 1, minutes = -current_time.minute)
		# cfg.set('next_post_time', int(goal_timestamp.timestamp()))
		# log.info('Starting loop at ' + goal_timestamp.strftime('%H:%M:%S'))
		# await asyncio.sleep((goal_timestamp - current_time).total_seconds())

bot = Bot()
bot.run(cfg["discord"]["token"])