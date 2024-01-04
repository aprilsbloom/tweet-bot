import asyncio
import shutil
import discord
import os
import traceback
import random
import string
import threading
import aiohttp
from datetime import datetime, timedelta
from pathlib import Path
from typing import Union
from discord.ext import commands, tasks
from httpx import AsyncClient, Response
from modules import post_twitter, post_mastodon, post_tumblr
from utils.globals import BASE_HEADERS, POST_HR_INTERVAL, POST_WB_INFO, MISC_WB_INFO, cfg, log

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

		current_time = datetime.now()
		goal_timestamp = current_time + timedelta(hours = 1, minutes = -current_time.minute)
		cfg.set('next_post_time', int(goal_timestamp.timestamp()))
		log.info('Starting loop at ' + goal_timestamp.strftime('%H:%M:%S'))

		await asyncio.sleep((goal_timestamp - current_time).total_seconds())

		post_loop.start()


@tasks.loop(hours = POST_HR_INTERVAL)
async def post_loop():
	# Set the next post time
	current_time = datetime.now()
	goal_timestamp = current_time + timedelta(hours = 4, minutes = -current_time.minute, seconds = -current_time.second, microseconds = -current_time.microsecond)
	cfg.set('next_post_time', int(goal_timestamp.timestamp()))

	# start post function on separate thread
	post_thread = threading.Thread(target = asyncio.run, args = (post))
	post_thread.start()
	post_thread.join()

async def post():
	try:
		print("")
		log.info('Running post loop...')

		client = AsyncClient()
		session = aiohttp.ClientSession()
		queue = cfg.get('queue')

		# Check to see if there are any posts in the queue
		if len(queue) == 0:
			await client.aclose()
			await session.close()
			return log.info("No posts in queue. Skipping...")

		# Check to see if every platform is disabled (we don't want to run)
		if not cfg.get('twitter.enabled') and not cfg.get('tumblr.enabled') and not cfg.get('mastodon.enabled'):
			await client.aclose()
			await session.close()
			return log.info("All platforms are disabled. Skipping...")

		# Initialize the post parameters to make it easier later on
		post = queue[0]
		caption = post.get('caption', '')
		alt_text = post.get('alt_text', '')
		author = post.get('author', '')
		emoji = post.get('emoji', '')
		catbox_url = post.get('catbox_url', '')
		orig_url = post.get('original_url', '')

		# Initialize job directory and assign random ID
		if os.path.exists("jobs/"):
			shutil.rmtree("jobs/")

		os.mkdir("jobs")
		job_id = "".join(random.choice(string.ascii_letters + string.digits) for i in range(32))

		# Initialize the webhook clients in a try/catch block in the event that it errors
		post_wb: discord.Webhook = ""
		misc_wb: discord.Webhook = ""

		try:
			if cfg.get('discord.post_notifs.enabled'):
				post_wb = discord.Webhook.from_url(cfg.get('discord.post_notifs.webhook'), session = session)

			if cfg.get('discord.misc_notifs.enabled'):
				misc_wb = discord.Webhook.from_url(cfg.get('discord.misc_notifs.webhook'), session = session)
		except:
			log.error(f"An error occurred while initializing the webhook client\n{traceback.format_exc()}")
			await client.aclose()
			await session.close()
			return


		# Download and write the gif to the system before posting, in order to ensure everything is legitimate
		# If an error occurs, i.e the web server times out, we want to catch it
		res: Response = ""

		try:
			res = await client.get(catbox_url, headers = BASE_HEADERS, timeout = 30)
		except:
			log.error(f"An error occurred while downloading the gif\n{traceback.format_exc()}")
			embed = discord.Embed(title = "Error", description = "An error occurred while downloading the gif.", color = discord.Color.from_str(cfg.get('discord.embed_colors.error')))
			embed.add_field(name = "Error", value = f"```{traceback.format_exc()}```", inline = False)
			await client.aclose()
			await session.close()
			return await misc_wb.send(embed = embed, username = MISC_WB_INFO['username'], avatar_url = MISC_WB_INFO['pfp'])


		# If the server returns a non-ok status code, we want to respond accordingly as well
		if res.status_code != 200:
			err_hdr = 'An error occurred while downloading the gif'
			err_dsc = f"The server returned a non-ok status code ({res.status_code})."

			log.error(f"{err_hdr}\n{err_dsc}")
			embed = discord.Embed(title = "Error", description = err_hdr, color = discord.Color.from_str(cfg.get('discord.embed_colors.error')))
			embed.add_field(name = "Error", value = f"```{err_dsc}```", inline = False)
			await misc_wb.send(embed = embed, username = MISC_WB_INFO['username'], avatar_url = MISC_WB_INFO['pfp'])

			# We also want to remove the tweet from the queue, so that the bot doesn't attempt to post it again
			queue.pop(0)
			cfg.set('queue', queue)

			await client.aclose()
			await session.close()
			return


		# Write the gif to the jobs directory
		with open(f"jobs/{job_id}.gif", "wb") as f:
			f.write(res.content)


		# Now, begin the actual posting.
		# Assign the post data to individual variables in order to make accessing the properties easier
		res_data = {}

		# Twitter
		if cfg.get('twitter.enabled'):
			log.info('Posting to Twitter...')
			try:
				res_data["twitter"] = await post_twitter(post, job_id)
			except:
				log.error(f"An error occurred while posting to Twitter\n{traceback.format_exc()}")
				res_data["twitter"] = False

		# Mastodon
		if cfg.get('mastodon.enabled'):
			log.info('Posting to Mastodon...')
			try:
				res_data["mastodon"] = await post_mastodon(post, job_id)
			except:
				log.error(f"An error occurred while posting to Mastodon\n{traceback.format_exc()}")
				res_data["mastodon"] = False

		# Tumblr
		if cfg.get('tumblr.enabled'):
			log.info('Posting to Tumblr...')
			try:
				res_data["tumblr"] = await post_tumblr(post, job_id)
			except:
				log.error(f"An error occurred while posting to Tumblr\n{traceback.format_exc()}")
				res_data["tumblr"] = False


		# Check to see the results of each function call, if any of them are false or None we don't want to count them
		# If the platforms array is empty, we want to return an error
		platforms = [key.title() for key in res_data.keys() if res_data[key] != False and res_data[key] != None]
		if len(platforms) == 0:
			log.error(f"An error occurred while posting the gif\nAll platforms failed to post.")

			if cfg.get('discord.misc_notifs.enabled'):
				embed = discord.Embed(title = "Error", description = "An error occurred while posting the gif.\nAll platforms failed to post.", color = discord.Color.from_str(cfg.get('discord.embed_colors.error')))
				await misc_wb.send(embed = embed, username = MISC_WB_INFO['username'], avatar_url = MISC_WB_INFO['pfp'])

			await client.aclose()
			await session.close()

			return

		embed = discord.Embed(title = "New post", color = discord.Color.from_str(cfg.get('discord.embed_colors.success')))
		embed.set_image(url = orig_url)

		if caption != '':
			embed.add_field(name = "Caption", value = caption, inline = False)

		embed.add_field(name = "Alt text", value = alt_text, inline = False)
		embed.add_field(name = "Gif URL", value = catbox_url, inline = False)
		embed.add_field(name = "Posted by", value = f'<@!{author}> - {emoji}', inline = False)

		linksStr = '\n'.join([f'- [{platform_name}]({res_data[platform_name.lower()]})' for platform_name in platforms])
		embed.add_field(name = "Post links", value = linksStr, inline = False)


		# Send the embed to the post notification webhook
		if cfg.get('discord.post_notifs.enabled'):
			role_to_ping = cfg.get('discord.post_notifs.role_to_ping')
			await post_wb.send(content = f"<@&{role_to_ping}>", embed = embed, username = POST_WB_INFO['username'], avatar_url = POST_WB_INFO['pfp'])

		await asyncio.sleep(3)


		# Send the embed to the misc notification webhook to alert the author that the post was successful
		if cfg.get('discord.misc_notifs.enabled'):
			await misc_wb.send(content = f"<@!{author}>", embed = embed, username = MISC_WB_INFO['username'], avatar_url = MISC_WB_INFO['pfp'])


		# Remove post from queue now that its been posted
		if len(queue) > 0:
			queue.pop(0)

		cfg.set('queue', queue)

		# Close the sessions since we're done with them
		await client.aclose()
		await session.close()
	except:
		log.error(f"An error occurred while running the post loop\n{traceback.format_exc()}")
		if client: await client.aclose()
		if session: await session.close()






token = cfg.get('discord.token')
if token == '':
	log.error('No token provided in config.json. Exiting...')
	exit()

bot = Bot()
bot.run(token)