import os
import discord
import traceback
import random
import string
import tweepy
from discord.ext import commands, tasks
from utils.config import fetch_data, write_data
from utils.logger import log
from utils.general import make_async_request

class Bot(commands.Bot):
	def __init__(self):
		super().__init__(
			intents = discord.Intents.default(),
			command_prefix = ''
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
		post_tweet.start()


@tasks.loop(hours = 2)
async def post_tweet():
	config = fetch_data()

	# if no posts in queue, log error, else fetch post
	if len(config['twitter']['post_queue']) == 0:
		return log.info('No posts found in the queue.')

	post = random.choice(config['twitter']['post_queue'])

	try:
		# make jobs directory and fetch the content of the actual gif
		if not os.path.exists('jobs/'):
			os.mkdir('jobs')

		job_id = ''.join(random.choice(string.ascii_letters + string.digits) for i in range(32))
		res_gif = await make_async_request(post.get('original_url', ''))

		# if gif returns anything other than 200 (ok status code) then return error
		if res_gif.status_code != 200:
			config['twitter']['post_queue'].remove(post)
			write_data(config)
			return log.error('Error occurred while fetching gif')

		# write content to file
		with open(f'jobs/{job_id}.gif', 'wb') as f:
			f.write(res_gif.content)

		# upload file to twitter and add alt text if present
		mediaID = v1.chunked_upload(filename = f'jobs/{job_id}.gif', media_category = "tweet_gif").media_id_string
		if post.get('alt_text', '') != '':
			v1.create_media_metadata(media_id = mediaID, alt_text = post.get('alt_text'))

		# post tweet and reply to it with url & emoji
		tweet = v2.create_tweet(text = post.get('caption', ''), media_ids = [ mediaID ])
		log.success(f'Successfully posted! https://twitter.com/i/status/{tweet[0]["id"]}')

		catbox_url = post.get('catbox_url')
		emoji = post.get('emoji')
		v2.create_tweet(text = f'{catbox_url} - {emoji}', in_reply_to_tweet_id = tweet[0]['id'])

		# remove post from queue now that its been posted
		config['twitter']['post_queue'].remove(post)
		write_data(config)
	except:
		log.error(f'An error occurred while attempting to post a tweet\n{traceback.format_exc()}')
		config['twitter']['post_queue'].remove(post)
		write_data(config)

	# remove all files in the jobs directory
	await remove_jobs()


async def remove_jobs():
	for file in os.listdir('jobs'):
		try:
			os.remove(f'jobs/{file}')
		except:
			pass

config = fetch_data()

# twitter
tweepy_auth = tweepy.OAuth1UserHandler(
	config['twitter']['consumer_key'],
	config['twitter']['consumer_secret'],
	config['twitter']['access_token'],
	config['twitter']['access_token_secret']
)
v1 = tweepy.API(tweepy_auth, wait_on_rate_limit=True)
v2 = tweepy.Client(
	consumer_key = config['twitter']['consumer_key'],
	consumer_secret = config['twitter']['consumer_secret'],
	access_token = config['twitter']['access_token'],
	access_token_secret=  config['twitter']['access_token_secret'],
	bearer_token = config['twitter']['bearer_token'],
	wait_on_rate_limit=True
)

# discord
bot = Bot()
bot.run(config['discord']['token'])