import discord
import os
import traceback
import random
import string
import tweepy
from pathlib import Path
from typing import Union
from discord.ext import commands, tasks
from httpx import AsyncClient, Response
from utils.config import load_config, write_config
from utils.general import create_embed
from utils.logger import Logger
from utils.constants import BASE_HEADERS, POST_WB_INFO, MISC_WB_INFO

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


@tasks.loop(hours = 2)
async def post_tweet_loop():
	config = load_config()
	client = AsyncClient()

	if len(config['twitter']['queue'] == 0):
		return log.info("No tweets in queue. Skipping...")

	post = config['twitter']['queue'][0]
	post_wb: discord.Webhook = ""
	misc_wb: discord.Webhook = ""

	# Initialize the webhook clients in a try/catch block in the event that it errors
	try:
		post_wb = discord.Webhook.from_url(config['discord']['post_notifs']['webhook'])
		misc_wb = discord.Webhook.from_url(config['discord']['misc_notifs']['webhook'])
	except:
		log.error(f"An error occurred while initializing the webhook client\n{traceback.format_exc()}")
		return

	try:
		# Initialize the jobs directory and the randomly generated ID, as we are using tweepy's file upload feature
		if not os.path.exists("jobs/"):
			os.mkdir("jobs")

		job_id = "".join(random.choice(string.ascii_letters + string.digits) for i in range(32))
		res: Response = ""

		caption = post.get("caption", "")
		alt_text = post.get("alt_text")
		catbox_url = post.get("catbox_url")
		emoji = post.get("emoji")

		# If an error occurs, i.e the web server times out, we want to catch it
		try:
			res = await client.get(post['catbox_url'], headers = BASE_HEADERS)
		except:
			log.error(f"An error occurred while downloading the gif\n{traceback.format_exc()}")
			embed = discord.Embed(title = "Error", description = "An error occurred while downloading the gif.", color = discord.Color.from_str(config["discord"]['embed_colors']['error']))
			embed.add_field(name = "Error", value = f"```{traceback.format_exc()}```", inline = False)
			return await misc_wb.send(embed = embed, username = MISC_WB_INFO['username'], avatar_url = MISC_WB_INFO['pfp'])


		# If the server returns a non-ok status code, we want to respond accordingly as well
		if res.status_code != 200:
			err_hdr = 'An error occurred while downloading the gif'
			err_dsc = f"The server returned a non-ok status code ({res.status_code})."

			log.error(f"{err_hdr}\n{err_dsc}")
			embed = discord.Embed(title = "Error", description = err_hdr, color = discord.Color.from_str(config["discord"]['embed_colors']['error']))
			embed.add_field(name = "Error", value = f"```{err_dsc}```", inline = False)
			await misc_wb.send(embed = embed, username = MISC_WB_INFO['username'], avatar_url = MISC_WB_INFO['pfp'])

			# We also want to remove the tweet from the queue, so that the bot doesn't attempt to post it again
			config['twitter']['queue'].pop(0)
			write_config(config)
			return


		# Write the gif to the jobs directory
		with open(f"jobs/{job_id}.gif", "wb") as f:
			f.write(res.content)

		mediaID = tw_v1.chunked_upload(
			filename = f"jobs/{job_id}.gif",
		 	media_category = "tweet_gif"
		).media_id_string

		if alt_text != "":
			tw_v1.create_media_metadata(
				media_id = mediaID,
				alt_text = alt_text
			)

		# post tweet and reply to it with url & emoji
		tweet = tw_v2.create_tweet(
			text = caption,
			media_ids = [mediaID]
		)

		tw_v2.create_tweet(
			text = f"{catbox_url} - {emoji}",
			in_reply_to_tweet_id = post[0]["id"]
		)

		# log message to console and send message in discord
		log.success(f'Successfully posted! https://twitter.com/i/status/{tweet[0]["id"]}')
		embed = create_embed(
			"Success",
			f"Successfully posted! https://twitter.com/i/status/{tweet[0]['id']}",
			"success"
		)

		if caption != "":
			embed.add_embed_field(
				name = 'Caption',
				value = caption,
				inline = False,
			)

		embed.add_embed_field(
			name = 'Alt text',
			value = alt_text,
			inline = False
		)

		embed.add_embed_field(
			name = 'Gif URL',
			value = catbox_url,
			inline = False,
		)

		embed.set_image(url = catbox_url)

		# Send a message to the post notifications channel if enabled
		if config['discord']['post_notifs']['enabled']:
			post_wb.add_embed(embed = embed)
			post_wb.send(embed = embed, username = POST_WB_INFO['username'], avatar_url = POST_WB_INFO['pfp'])

		# Send a message within the server where the tweets are posted from if enabled
		if config['discord']['misc_notifs']['enabled']:
			misc_wb.add_embed(embed = embed)
			misc_wb.send(embed = embed, username = MISC_WB_INFO['username'], avatar_url = MISC_WB_INFO['pfp'])

		# remove post from queue now that its been posted
		config["twitter"]["post_queue"].remove(post)
		write_config(config)
	except:
		log.error(f"An error occurred within the tweet-posting loop\n{traceback.format_exc()}")

	await client.aclose()

# Twitter API
twitter_auth = tweepy.OAuth1UserHandler(
	config["twitter"]["consumer_key"],
	config["twitter"]["consumer_secret"],
	config["twitter"]["access_token"],
	config["twitter"]["access_token_secret"],
)

tw_v1 = tweepy.API(twitter_auth, wait_on_rate_limit = True)
tw_v2 = tweepy.Client(
	consumer_key = config["twitter"]["consumer_key"],
	consumer_secret = config["twitter"]["consumer_secret"],
	access_token = config["twitter"]["access_token"],
	access_token_secret = config["twitter"]["access_token_secret"],
	bearer_token = config["twitter"]["bearer_token"],
	wait_on_rate_limit = True,
)


bot = Bot()
bot.run(config['discord']['token'])