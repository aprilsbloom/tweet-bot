import os
import discord
import traceback
import random
import string
import tweepy
import asyncio
from discord_webhook import DiscordWebhook, DiscordEmbed
from discord.ext import commands, tasks
from utils.config import fetch_data, write_data
from utils.logger import log
from utils.general import make_async_request
from datetime import datetime


class Bot(commands.Bot):
	def __init__(self):
		super().__init__(
			intents = discord.Intents.default(),
			command_prefix = ""
		)

	async def setup_hook(self):
		await self.setupCommands("cogs")

		try:
			synced = await bot.tree.sync()
			log.info(f"Synced {len(synced)} commands")
		except Exception:
			log.error(f"An error has occurred while syncing commands.\n{traceback.format_exc()}")
			return

	async def setupCommands(self, directory):
		for root, dirs, files in os.walk(directory):
			for file in files:
				if file.endswith(".py"):
					cog_path = (os.path.join(root, file).replace(os.sep, ".").rstrip(".py"))
					try:
						await self.load_extension(cog_path)
					except:
						log.error(f'Unable to load {cog_path}\n{traceback.format_exc()}')
			for dir in dirs:
				await self.setupCommands(os.path.join(root, dir))

	async def on_ready(self):
		await self.wait_until_ready()
		log.success(f"Logged in as {self.user}.")

		current_time = datetime.now()

		# determine goal hour since its only 0-23, depending on the time ran it may fuck shit up
		goal_hr = 0
		if (current_time.hour + 1) > 23:
			goal_hr = 0
		else:
			goal_hr = current_time.hour + 1

		# work out the delay in seconds
		start_time = current_time.replace(hour = goal_hr, minute = 0, second = 0)
		delay = (start_time - current_time).total_seconds()
		await asyncio.sleep(delay)

		post_tweet.start()


@tasks.loop(hours = 2)
async def post_tweet():
	config = fetch_data()
	post_webhook = ""
	notif_webhook = ""

	# if no posts in queue, log error, else fetch post
	if len(config["twitter"]["post_queue"]) == 0:
		return log.info("No posts found in the queue.")

	post = config["twitter"]["post_queue"][0]

	try:
		post_webhook: DiscordWebhook = DiscordWebhook(
			url = config["discord"]["post_webhook"],
			content = f'<@{post["author"]}>',
			avatar_url = "https://cdn.discordapp.com/avatars/980746909222338580/840892f27a807f8ad37ed1f23f56d95d.webp?size=4096",
			username = "Tweet Bot",
		)
		notif_webhook: DiscordWebhook = DiscordWebhook(
			url = config["discord"]["notif_webhook"],
			content = f"<@&{config['discord']['role_to_ping']}>",
			avatar_url = "https://pbs.twimg.com/profile_images/3424946333/6ead4754bb47e8ec302c1d536cb693b1_reasonably_small.gif",
			username = "gifkitties",
		)
	except:
		log.error(f"An error occurred while initializing the webhook client\n{traceback.format_exc()}")
		return

	try:
		# make jobs directory and fetch the content of the actual gif
		if not os.path.exists("jobs/"):
			os.mkdir("jobs")

		job_id = "".join(random.choice(string.ascii_letters + string.digits) for i in range(32))

		try:
			res_gif = await make_async_request(post.get("catbox_url", ""))
		except:
			embed = DiscordEmbed(
				title = "Error",
				description = f'An error occurred while fetching the gif\n```{traceback.format_exc()}```',
				color = discord.Color.from_str(config["discord"]["embed_colors"]["success"]).value,
			)
			post_webhook.add_embed(embed = embed)
			return post_webhook.execute()

		# if gif returns anything other than 200 (ok status code) then return error
		if res_gif.status_code!= 200:
			config["twitter"]["post_queue"].remove(post)
			write_data(config)
			log.error(f'An error occurred while fetching gif: {post["catbox_url"]} returned a non-ok status code')

			embed = DiscordEmbed(
				title = "Error",
				description = f'An error occurred while fetching gif: {post["catbox_url"]} returned a non-ok status code',
				color = discord.Color.from_str(config["discord"]["embed_colors"]["success"]).value,
			)
			post_webhook.add_embed(embed = embed)
			return post_webhook.execute()

		# write gif to file
		with open(f"jobs/{job_id}.gif", "wb") as f:
			f.write(res_gif.content)

		# upload file to twitter and add alt text if present
		mediaID = twitter_v1.chunked_upload(
			filename = f"jobs/{job_id}.gif",
		 	media_category = "tweet_gif"
		).media_id_string

		if post.get("alt_text", "")!= "":
			twitter_v1.create_media_metadata(
				media_id = mediaID,
				alt_text = post.get("alt_text")
			)

		# post tweet and reply to it with url & emoji
		tweet = twitter_v2.create_tweet(
			text = post.get("caption", ""),
			media_ids = [mediaID]
		)

		catbox_url = post.get("catbox_url")
		emoji = post.get("emoji")
		twitter_v2.create_tweet(
			text = f"{catbox_url} - {emoji}",
			in_reply_to_tweet_id = tweet[0]["id"]
		)

		# log message to console and send message in discord
		log.success(f'Successfully posted! https://twitter.com/i/status/{tweet[0]["id"]}')
		embed = DiscordEmbed(
			title = "Success",
			description = f'Successfully posted!\n[View tweet](https://twitter.com/i/status/{tweet[0]["id"]})',
			color = discord.Color.from_str(config["discord"]["embed_colors"]["success"]).value,
		)

		if post.get("caption", "") != "":
			embed.add_embed_field(
				name = 'Caption',
				value = post.get('caption', ''),
				inline = False,
			)

		embed.add_embed_field(
			name = 'Alt text',
			value = post.get("alt_text"),
			inline = False
		)

		embed.add_embed_field(
			name = 'Gif URL',
			value = catbox_url,
			inline = False,
		)

		embed.set_image(url = catbox_url)

		post_webhook.add_embed(embed = embed)
		post_webhook.execute()

		# send message to the notif channel
		notif_webhook.add_embed(embed = embed)
		notif_webhook.execute()

		# remove post from queue now that its been posted
		config["twitter"]["post_queue"].remove(post)
		write_data(config)
	except:
		# log error to console and send to discord
		log.error(f"An error occurred while attempting to post a tweet\n```{traceback.format_exc()}```")

		embed = DiscordEmbed(
			title = "Error",
			description = f"An error occurred while attempting to post a tweet\n```{traceback.format_exc()}```",
			color = discord.Color.from_str(config["discord"]["embed_colors"]["error"]).value,
		)
		embed.set_image(url = post["catbox_url"])

		post_webhook.add_embed(embed = embed)
		post_webhook.execute

		# remove post from queue
		config["twitter"]["post_queue"].remove(post)
		write_data(config)

	# remove all files in the jobs directory
	await remove_jobs()


async def remove_jobs():
	for file in os.listdir("jobs"):
		try:
			os.remove(f"jobs/{file}")
		except:
			pass

config = fetch_data()

# twitter
twitter_auth = tweepy.OAuth1UserHandler(
	config["twitter"]["consumer_key"],
	config["twitter"]["consumer_secret"],
	config["twitter"]["access_token"],
	config["twitter"]["access_token_secret"],
)

twitter_v1 = tweepy.API(twitter_auth, wait_on_rate_limit = True)
twitter_v2 = tweepy.Client(
	consumer_key = config["twitter"]["consumer_key"],
	consumer_secret = config["twitter"]["consumer_secret"],
	access_token = config["twitter"]["access_token"],
	access_token_secret = config["twitter"]["access_token_secret"],
	bearer_token = config["twitter"]["bearer_token"],
	wait_on_rate_limit = True,
)

# discord
bot = Bot()
bot.run(config["discord"]["token"])
