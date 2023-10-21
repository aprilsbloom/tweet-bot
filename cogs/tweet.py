import discord
import re
import tweepy
from discord.ext import commands
from utils.config import fetch_data, write_data
from utils.general import make_async_request, handleResponse

# regexes
TENOR_REGEX = r'(?i)\b((https?://media[.]tenor[.]com/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))[.]gif)'
CLEAN_URL_REGEX = r"\?.*$"

# file size limits
FILESIZE_LIMIT_TWITTER = 15728640

# catbox (file host) api
CATBOX_URL = "https://catbox.moe/user/api.php"


class Tweet(commands.Cog):
	def __init__(self, bot: commands.Bot):
		self.bot = bot
		self.config = fetch_data()

		self.tweepy_auth = tweepy.OAuth1UserHandler(
			self.config['twitter']['consumer_secret'],
			self.config['twitter']['consumer_secret'],
			self.config['twitter']['access_token'],
			self.config['twitter']['bearer_token']
		)
		self.v1 = tweepy.API(self.tweepy_auth, wait_on_rate_limit=True)
		self.v2 = tweepy.Client(
			consumer_key = self.config['twitter']['consumer_secret'],
			consumer_secret = self.config['twitter']['consumer_secret'],
			access_token = self.config['twitter']['access_token'],
			access_token_secret=  self.config['twitter']['bearer_token'],
			bearer_token = self.config['twitter']['bearer_token'],
			wait_on_rate_limit=True
		)


	@discord.app_commands.command(name = 'tweet', description = 'Post a tweet')
	@discord.app_commands.describe(
		url = 'The URL of the gif you want to tweet (please remove any additional text in the URL)',
		alt_text = 'The alt text of the tweet (please be as informative as possible)',
		caption = 'The caption of the tweet',
	)
	async def tweet(
		self,
		interaction: discord.Interaction,
		url: str,
		alt_text: str,
		caption: str = ''
	):
		config = fetch_data()
		bot_info = await self.bot.application_info()

		# check if user is authed
		if interaction.user.id not in config['discord']['authed_users'] and interaction.user.id != bot_info.owner.id:
			return await handleResponse(
				interaction = interaction,
				config = config,
				content = 'You do not have permission to run this command.\nPlease ask an administrator for access if you believe this to be in error.',
				responseType = 'error'
			)

		# check if user has an emoji set
		if str(interaction.user.id) not in config['discord']['emojis']:
			return await handleResponse(
				interaction = interaction,
				config = config,
				content = 'You do not have an emoji set. Please use /emoji set before posting again.',
				responseType = 'error'
			)

		# fetch the posters emoji and remove any parameters from the url
		emoji = config['discord']['emojis'][str(interaction.user.id)].encode('utf-16', 'surrogatepass').decode('utf-16')
		clean_url = re.sub(CLEAN_URL_REGEX, "", url)

		await handleResponse(
			interaction = interaction,
			config = config,
			content = 'Determining if the gif is valid...',
			responseType = 'info'
		)

		# determine the real url of the given gif depending on what site is picked
		if clean_url.startswith('https://tenor.com/view'):
			response = await make_async_request(url)
			url = re.findall(TENOR_REGEX, response.text)[0][0]
		elif clean_url.startswith('https://giphy.com/gifs/'):
			res = await make_async_request(url)
			tmp_url = res.text.split('property="og:image" content="')[1].split('"')[0]

			if tmp_url == 'https://giphy.com/static/img/giphy-be-animated-logo.gif':
				return handleResponse(
					interaction = interaction,
					config = config,
					content = 'Unable to find the gif from the link provided.',
					responseType = 'error'
				)
			else:
				url = tmp_url
		elif clean_url.endswith('.gif'):
			url = url
		else:
			return await handleResponse(
				interaction = interaction,
				config = config,
				content = 'The URL you entered is currently not supported by the bot. At the moment, we only support Tenor, Giphy, and URLs that end in .gif',
				responseType = 'error'
			)

		# reassign the clean url of the gif
		clean_url = re.sub(CLEAN_URL_REGEX, "", url)

		for post in config['twitter']['post_queue']:
			if post['original_url'] == clean_url:
				return await handleResponse(
					interaction = interaction,
					config = config,
					content = 'The URL you entered is already in the queue.',
					responseType = 'error'
				)

		# check if file is bigger than what is allowed
		res_head = await make_async_request(
			url,
			method = 'HEAD'
		)

		# sites can return variations of the header, so we have to have checks for both capitalizations
		if res_head.headers.get('content-length'):
			file_size = res_head.headers.get('content-length')
		elif res_head.headers.get('Content-Length'):
			file_size = res_head.headers.get('Content-Length')
		else:
			res_gif = await make_async_request(url)
			file_size = len(res_gif.content)

		if int(file_size) > FILESIZE_LIMIT_TWITTER:
			return await handleResponse(
				interaction = interaction,
				config = config,
				content = 'The gif you uploaded is too big. Please compress your file to below 15MB in size, and try again.',
				responseType = 'error'
			)

		# upload file to catbox.moe
		res_catbox = await make_async_request(
			url = CATBOX_URL,
			method = 'POST',
			data = {
                'reqtype': 'urlupload',
                'userhash': '',
                'url': url
            },
		)

		# handle errors since it doesn't use json (hate)
		if 'Something went wrong' in res_catbox.text:
			return await handleResponse(
				interaction = interaction,
				config = config,
				content = 'An unknown error occurred when attempting to upload your gif to [catbox](https://catbox.moe). If this error persists, please contact an administrator.',
				responseType = 'error'
			)

		# append data to post queue and write it
		config['twitter']['post_queue'].append(
			{
				'original_url': clean_url,
				'catbox_url': res_catbox.text,
				'author': interaction.user.id,
				'emoji': emoji,
				'caption': caption,
				'alt_text': alt_text
			}
		)
		write_data(config)

		# return embed saying thing was added to queue
		return await handleResponse(
			interaction = interaction,
			config = config,
			content = 'Your post has been added to the queue.',
			responseType = 'success',
			image_url = res_catbox.text
		)

	@tweet.error
	async def tweet_error(self, interaction: discord.Interaction, error):
		config = fetch_data()
		return await handleResponse(
			interaction = interaction,
			config = config,
			content = f'An unknown error has occurred:\n```\n{error}\n```',
			responseType = 'error'
		)

# Cog setup
async def setup(bot: commands.Bot):
	await bot.add_cog(Tweet(bot))