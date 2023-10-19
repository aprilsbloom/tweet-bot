import discord
import re
import httpx
import filetype
import tweepy
import random
import string
import os
from discord.ext import commands
from utils.config import fetch_data

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


	@discord.app_commands.command(name = 'tweet', description = 'a')
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
		job_id = ''.join(random.choice(string.ascii_letters + string.digits) for i in range(32))
		config = fetch_data()
		bot_info = await self.bot.application_info()

		if not os.path.exists('jobs/'):
			os.mkdir('jobs')

		# check if user is authed
		if interaction.user.id not in config['discord']['authed_users'] and interaction.user.id != bot_info.owner.id:
			return await self.handleResponse(
				interaction = interaction,
				config = config,
				content = 'You do not have permission to run this command.\nPlease ask an administrator for access if you believe this to be in error.',
				responseType = 'error'
			)

		# check if user has an emoji set
		if str(interaction.user.id) not in config['discord']['emojis']:
			return await self.handleResponse(
				interaction = interaction,
				config = config,
				content = 'You do not have an emoji set. Please use /emoji set before posting again.',
				responseType = 'error'
			)

		# fetch the posters emoji and remove any parameters from the url
		emoji = config['discord']['emojis'][str(interaction.user.id)].encode('utf-16', 'surrogatepass').decode('utf-16')
		clean_url = re.sub(CLEAN_URL_REGEX, "", url)

		# determine the real url of the given gif depending on what site is picked
		if clean_url.startswith('https://tenor.com/view'):
			response = await self.make_async_request(url)
			url = re.findall(TENOR_REGEX, response.text)[0][0]
		elif url.startswith('https://giphy.com/gifs/'):
			res = await self.make_async_request(url)
			tmp_url = res.text.split('property="og:image" content="')[1].split('"')[0]

			if tmp_url == 'https://giphy.com/static/img/giphy-be-animated-logo.gif':
				return self.handleResponse(
					interaction = interaction,
					config = config,
					content = 'Unable to find the gif from the link provided.',
					responseType = 'error'
				)
			else:
				url = tmp_url

		# check if file is bigger than what is allowed
		res_head = await self.make_async_request(
			url,
			method = 'HEAD'
		)

		# sites can return variations of the header, so we have to have checks for both capitalizations
		if res_head.headers.get('content-length'):
			file_size = res_head.headers.get('content-length')
		elif res_head.headers.get('Content-Length'):
			file_size = res_head.headers.get('Content-Length')
		else:
			res_gif = await self.make_async_request(url)
			file_size = len(res_gif.content)

		if int(file_size) > FILESIZE_LIMIT_TWITTER:
			return await self.handleResponse(
				interaction = interaction,
				config = config,
				content = 'The gif you uploaded is too big. Please compress your file to below 10MB in size, and try again.',
				responseType = 'error'
			)

		# check if res_gif is assigned because we do it in the file_size check in order to get the byte length
		if not res_gif:
			res_gif = await self.make_async_request(url)

		# upload file to catbox.moe
		res_catbox = await self.make_async_request(
			url = CATBOX_URL,
			method = 'POST',
			data = {
                'reqtype': 'urlupload',
                'userhash': '',
                'url': url
            },
		)

		if 'Something went wrong' in res_catbox.text:
			return await self.handleResponse(
				interaction = interaction,
				config = config,
				content = 'An unknown error occurred when attempting to upload your gif to [catbox](https://catbox.moe). If this error persists, please contact an administrator.',
				responseType = 'error'
			)

		# post tweet
		with open(f'jobs/{job_id}.gif', 'wb') as f:
			f.write(res_gif.content)

		mediaID = self.v1.chunked_upload(filename = f'jobs/{job_id}.gif', media_category = "tweet_gif").media_id_string
		if alt_text != '':
			self.v1.create_media_metadata(media_id = mediaID, alt_text = alt_text)

		post = self.v2.create_tweet(text = caption, media_ids = [ mediaID ])
		self.v2.create_tweet(text = f'{url} - {emoji}', in_reply_to_tweet_id = post[0]['id'])

		try:
			os.remove(f'jobs/{job_id}.gif')
		except:
			pass


		embed = discord.Embed(title = 'Success', description = f'[View Tweet](https://twitter.com/i/status/{post[0]["id"]})', color = discord.Color.from_str(config['discord']['embed_colors']['success']))
		embed.set_image(url = url)
		await interaction.edit_original_response(embed=embed)

	async def make_async_request(
		self,
		url: str,
		headers: dict = {},
		method: str = 'GET',
		data: dict = {},
		json: dict = {},
	):
		async with httpx.AsyncClient() as client:
			response = await client.request(
				url = url,
				headers = headers,
				method = method,
				data = data,
				json = json
			)

		return response

	async def handleResponse(
		self,
		interaction: discord.Interaction,
		config: dict,
		content: str,
		responseType: str
	):
		embed = discord.Embed(description = content)

		# embed title and color
		match responseType:
			case 'success':
				embed.title = 'Success'
				embed.color = discord.Color.from_str(config['discord']['embed_colors']['success'])
			case 'info':
				embed.title = 'Info'
				embed.color = discord.Color.from_str(config['discord']['embed_colors']['info'])
			case 'error':
				embed.title = 'Error'
				embed.color = discord.Color.from_str(config['discord']['embed_colors']['error'])

		# respond with the embed
		if interaction.response.is_done():
			return await interaction.edit_original_response(embed = embed)
		else:
			return await interaction.response.send_message(embed = embed)



# Cog setup
async def setup(bot: commands.Bot):
	await bot.add_cog(Tweet(bot))