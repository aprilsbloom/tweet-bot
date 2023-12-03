import asyncio
import shutil
import discord
import os
import traceback
import random
import string
import tweepy
import threading
import pytumblr
import aiohttp
from datetime import datetime, timedelta
from mastodon import Mastodon
from pathlib import Path
from typing import Union
from discord.ext import commands, tasks
from httpx import AsyncClient, Response
from tenacity import retry, stop_after_attempt, retry_if_result
from utils.globals import BASE_HEADERS, CAT_HASHTAGS, POST_HR_INTERVAL, POST_WB_INFO, MISC_WB_INFO, cfg, log

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

		# Determine goal hour
		# current_time = datetime.now()
		# goal_timestamp = current_time + timedelta(hours = 1, minutes = -current_time.minute)
		# delay = (goal_timestamp - current_time).total_seconds()

		# cfg.set('next_post_time', int(goal_timestamp.timestamp()))
		# log.info('Starting loop at ' + goal_timestamp.strftime('%H:%M:%S'))

		# await asyncio.sleep(delay)

		post_loop.start()


@tasks.loop(hours = POST_HR_INTERVAL)
async def post_loop():
	# start post function on separate thread
	post_thread = threading.Thread(target = asyncio.run, args = (post(),))
	post_thread.start()

	# wait for thread to finish
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
			res_data["twitter"] = await post_twitter(post, job_id)

		await asyncio.sleep(5)


		# Tumblr
		if cfg.get('tumblr.enabled'):
			log.info('Posting to Tumblr...')
			res_data["tumblr"] = await post_tumblr(post, job_id)

		await asyncio.sleep(5)


		# Mastodon
		# if config["mastodon"]["enabled"]:
		# 	res_data["mastodon"] = await post_mastodon(config, post, job_id)

		# await asyncio.sleep(5)


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

		# Set the next post time
		current_time = datetime.now()
		goal_timestamp = current_time + timedelta(hours = 1, minutes = -current_time.minute, seconds = -current_time.second, milliseconds=-current_time.microsecond, microseconds = -current_time.microsecond)
		cfg.set('next_post_time', int(goal_timestamp.timestamp()))
	except:
		log.error(f"An error occurred while running the post loop\n{traceback.format_exc()}")
		if client: await client.aclose()
		if session: await session.close()

@retry(stop=stop_after_attempt(3), retry = retry_if_result(lambda result: result is False))
async def post_twitter(post, job_id):
	# Twitter API clients
	try:
		tw_auth = tweepy.OAuth1UserHandler(
			cfg.get('twitter.consumer_key'),
			cfg.get('twitter.consumer_secret'),
			cfg.get('twitter.access_token'),
			cfg.get('twitter.access_token_secret'),
		)

		tw_v1 = tweepy.API(tw_auth, wait_on_rate_limit = True)
		tw_v2 = tweepy.Client(
			consumer_key = cfg.get('twitter.consumer_key'),
			consumer_secret = cfg.get('twitter.consumer_secret'),
			access_token = cfg.get('twitter.access_token'),
			access_token_secret = cfg.get('twitter.access_token_secret'),
			bearer_token = cfg.get('twitter.bearer_token'),
			wait_on_rate_limit = True,
		)
	except:
		log.error(f"An error occurred while initializing the Twitter API clients\n{traceback.format_exc()}")
		return


	# Assign the post data to individual variables in order to make accessing the properties easier
	caption = post.get('caption', '')
	alt_text = post.get('alt_text', '')
	emoji = post.get('emoji', '')
	catbox_url = post.get('catbox_url', '')


	# Upload gif to twitter
	mediaID = tw_v1.chunked_upload(
		filename = f"jobs/{job_id}.gif",
		media_category = "tweet_gif"
	).media_id_string

	if alt_text != "":
		tw_v1.create_media_metadata(
			media_id = mediaID,
			alt_text = alt_text
		)

	# Post tweet and reply to it with url & emoji
	tweet = tw_v2.create_tweet(
		text = caption,
		media_ids = [mediaID]
	)

	tw_v2.create_tweet(
		text = f"{catbox_url} - {emoji}",
		in_reply_to_tweet_id = tweet[0]["id"]
	)

	log.success(f'Successfully posted to Twitter! https://twitter.com/i/status/{tweet[0]["id"]}')
	return f"https://twitter.com/i/status/{tweet[0]['id']}"


@retry(stop=stop_after_attempt(3), retry = retry_if_result(lambda result: result is False))
async def post_mastodon(post, job_id):
	# Mastodon API client
	mstdn: Mastodon = ""

	try:
		mstdn = Mastodon(
			client_id = cfg.get('mastodon.client_id'),
			client_secret = cfg.get('mastodon.client_secret'),
			access_token = cfg.get('mastodon.access_token'),
			api_base_url = cfg.get('mastodon.api_url')
		)
	except:
		log.error(f"An error occurred while initializing the Mastodon API client\n{traceback.format_exc()}")
		return

	# Assign the post data to individual variables in order to make accessing the properties easier
	caption = post.get('caption', '')
	alt_text = post.get('alt_text', '')
	emoji = post.get('emoji', '')
	catbox_url = post.get('catbox_url', '')


	# Post to mastodon
	media = mstdn.media_post(f"jobs/{job_id}.gif", mime_type = "image/gif", description=alt_text)
	post = mstdn.status_post(
		status = caption,
		media_ids = [media]
	)

	mstdn.status_post(
		status = f"{catbox_url} - {emoji}",
		in_reply_to_id = post["id"]
	)

	log.success(f'Successfully posted to Mastodon! {post["url"]}')
	return post['url']


@retry(stop=stop_after_attempt(3), retry = retry_if_result(lambda result: result is False))
async def post_tumblr(post, job_id):
	# Tumblr API client
	tmblr: pytumblr.TumblrRestClient = ""

	try:
		tmblr = pytumblr.TumblrRestClient(
			cfg.get('tumblr.consumer_key'),
			cfg.get('tumblr.consumer_secret'),
			cfg.get('tumblr.oauth_token'),
			cfg.get('tumblr.oauth_secret')
		)
	except:
		log.error(f"An error occurred while initializing the Tumblr API client\n{traceback.format_exc()}")
		return

	# Assign the post data to individual variables in order to make accessing the properties easier
	caption = post.get('caption', '')
	alt_text = post.get('alt_text', '')
	emoji = post.get('emoji', '')
	catbox_url = post.get('catbox_url', '')

	newCaption = ''
	if caption != '':
		newCaption = f"{caption} <br><br>"

	newCaption += f'<strong>Alt text:</strong> {alt_text} <br><br><strong>Gif URL:</strong> {catbox_url} <br><br><strong>Posted by:</strong> {emoji}'


	# Post to tumblr
	blog_name = cfg.get('tumblr.blog_name')
	res = tmblr.create_photo(
		caption = newCaption,
		tags = [f'posted-by-{emoji}'] + CAT_HASHTAGS,
		data = f"jobs/{job_id}.gif",
		state = 'published',
		blogname = blog_name,
		slug = job_id
	)

	log.success(f'Successfully posted to Tumblr! https://{blog_name}.tumblr.com/post/{res["id"]}')
	return f'https://{blog_name}.tumblr.com/post/{res["id"]}'


bot = Bot()
bot.run(cfg.get('discord.token'))