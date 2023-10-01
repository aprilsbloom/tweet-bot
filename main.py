import os
import traceback
import filetype
import re
import discord
import tweepy
import requests
from typing import Union, Optional
from discord.ext import commands
from datetime import datetime
from utils import Logger, fetch_data, write_data

log = Logger()
config = fetch_data()

# Discord
token = config['discord']['token']
intents = discord.Intents.default()
bot = commands.Bot(command_prefix = '', intents = intents)

# Twitter
CONSUMER_KEY = config['twitter']['consumer_key']
CONSUMER_SECRET = config['twitter']['consumer_secret']
ACCESS_TOKEN = config['twitter']['access_token']
ACCESS_TOKEN_SECRET = config['twitter']['access_token_secret']
BEARER_TOKEN = config['twitter']['bearer_token']

tweepy_auth = tweepy.OAuth1UserHandler(CONSUMER_KEY, CONSUMER_SECRET, ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
v1 = tweepy.API(tweepy_auth, wait_on_rate_limit=True)
v2 = tweepy.Client(consumer_key=CONSUMER_KEY, consumer_secret=CONSUMER_SECRET, access_token=ACCESS_TOKEN, access_token_secret=ACCESS_TOKEN_SECRET, bearer_token=BEARER_TOKEN, wait_on_rate_limit=True)

@bot.event
async def on_ready():
	os.system('cls' if os.name == 'nt' else 'clear')
	log.info(f'Logged in as {bot.user}')

	try:
		synced = await bot.tree.sync()
		log.info(f'Synced {len(synced)} commands')
	except Exception:
		log.error(f'An error has occurred while syncing commands.\n{traceback.format_exc()}')
		return

async def parseURL(interaction, url, caption, urlType, alt_text, emoji):
	gifURL = ''

	try:
		if urlType == 'gif':
			gifURL = url
		elif urlType == 'tenor':
			r = requests.get(url)
			regex = r'(?i)\b((https?://media[.]tenor[.]com/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))[.]gif)'
			gifURL = re.findall(regex, r.text)[0][0]
		elif urlType == 'giphy':
			r = requests.get(url)
			gifURL = r.text.split('property="og:image" content="')[1].split('"')[0]

			if gifURL == 'https://giphy.com/static/img/giphy-be-animated-logo.gif':
				return await handleError(interaction, 'Unable to find the gif from the link provided.', 'response')
	except:
		return await handleError(interaction=interaction, errorType='response', errorText=f'An error has occurred.\n\n```{traceback.format_exc()}```')

	r = requests.get(gifURL)
	if r.status_code == 200:
		with open('gif.gif', 'wb') as f:
			f.write(r.content)

		kind = filetype.guess('gif.gif')
		if kind is None or kind.extension != 'gif':
			return await handleError(interaction=interaction, errorType='response', errorText='The file provided is not a gif.')

		embed = discord.Embed(title = 'Info', description = 'Downloaded gif.', color = discord.Color.from_str(config['discord']['embed_colors']['info']))
		await interaction.response.send_message(embed = embed)

		await postGif(interaction, caption, alt_text, emoji)
	else:
		return await handleError(interaction=interaction, errorType='response', errorText='Unable to download gif.')

async def postGif(interaction, caption, alt_text, emoji):
	config = fetch_data()

	channel = bot.get_channel(config['discord']['archive_channel_id'])

	try:
		msg = await channel.send(file=discord.File('gif.gif'))
	except:
		return await handleError(interaction=interaction, errorType='edit', errorText=f'An error has occured when attempting to backup the gif before posting.\nDiscord is saying the gif is >10MB (their current filesize limit for bots for whatever reason lol)\nPlease compress your gif before trying again.\n\n```{traceback.format_exc()}```')

	url = msg.attachments[0].url

	try:
		gif_res = v1.chunked_upload(filename='gif.gif', media_category="tweet_gif").media_id_string

		if alt_text != '':
			v1.create_media_metadata(media_id=gif_res, alt_text=alt_text)

		if os.path.exists('gif.gif') and os.path.isfile('gif.gif'):
			os.remove('gif.gif')

		# post gif
		try:
			post = v2.create_tweet(text=caption, media_ids=[gif_res])
			v2.create_tweet(text=f'{url} - {emoji}', in_reply_to_tweet_id=post[0]['id'])

			embed = discord.Embed(title='Success', description=f'[View Tweet](https://twitter.com/i/status/{post[0]["id"]})', color = discord.Color.from_str(config['discord']['embed_colors']['success']))
			embed.set_image(url=url)
			await interaction.edit_original_response(embed=embed)

		except:
			return await handleError(interaction=interaction, errorType='edit', errorText=f'An error has occured when attempting to post the tweet.\n\n```{traceback.format_exc()}```')
	except:
		errorMsg = traceback.format_exc()

		if 'File size exceeds 15728640 bytes.' in errorMsg:
			errorMsg = 'The gif provided is over 15MB.\nPlease try again with a smaller gif, or compress the file.'

		return await handleError(interaction=interaction, errorText=f'An error has occurred.\n\n```{errorMsg}```')

async def handleError(interaction: discord.Interaction, errorText='', errorType='edit'):
	embed = discord.Embed(title = 'Error', description = errorText, color = discord.Color.from_str(config['discord']['embed_colors']['error']))

	if errorType == 'response':
		try:
			await interaction.response.send_message(embed=embed)
		except:
			await interaction.edit_original_response(embed=embed)
	elif errorType == 'edit':
		await interaction.edit_original_response(embed = embed)


@bot.tree.command(name = 'change_emoji')
@discord.app_commands.describe(emoji = 'The emoji you want to append to your own posts')
async def set_emoji(interaction: discord.Interaction, emoji: str):
	config = fetch_data()

	bot_info = await bot.application_info()
	owner_id = bot_info.owner.id

	if interaction.user.id not in config['discord']['authed_users'] and interaction.user.id != owner_id:
		return await handleError(interaction, 'You do not have permission to run this command.\nPlease ask an administrator for access if you believe this to be in error.', 'response')

	config['discord']['emojis'][str(interaction.user.id)] = emoji
	write_data(config)

	embed = discord.Embed(title = 'Success', description = f'Your emoji has been set to {emoji}', color = discord.Color.from_str(config['discord']['embed_colors']['success']))
	await interaction.response.send_message(embed = embed)

@bot.tree.command(name = 'view_emojis')
@discord.app_commands.describe(user = 'The user whos emoji you wish to view')
async def view_emojis(interaction, user: Optional[discord.Member] = None):
	config = fetch_data()
	emojiDict = config['discord']['emojis']

	if user is None:
		embed = discord.Embed(title = 'Emojis', description = '', color = discord.Color.from_str(config['discord']['embed_colors']['info']))

		if len(emojiDict) == 0:
			return await handleError(interaction, 'No emojis have been set.\nPlease use /set_emoji to set your own emoji.', 'response')

		for user in emojiDict:
			embed.description += f'**<@{user}>** - {emojiDict[user]}\n'

		await interaction.response.send_message(embed = embed)
	else:
		if str(user.id) in emojiDict:
			member = await bot.fetch_user(user.id)
			discriminator = member.discriminator
			name = member.name

			if discriminator == '0':
				username = f'@{name}'
			else:
				username = f'{name}#{discriminator}'

			embed = discord.Embed(title = f'Emoji for {username}', description = emojiDict[str(user.id)], color = discord.Color.from_str(config['discord']['embed_colors']['info']))
			await interaction.response.send_message(embed = embed)
		else:
			return await handleError(interaction, f'<@{user.id}> does not have an emoji set.', 'response')


@bot.tree.command(name = 'tweet')
@discord.app_commands.describe(url = 'The gif URL you want to tweet', caption = 'The caption of the tweet', alt_text = 'The alt text of the tweet')
async def tweet(interaction: discord.Interaction, url: str, caption: str = '', alt_text: str = ''):
	config = fetch_data()

	bot_info = await bot.application_info()
	owner_id = bot_info.owner.id

	if interaction.user.id not in config['discord']['authed_users'] and interaction.user.id != owner_id:
		return await handleError(interaction, 'You do not have permission to run this command.\nPlease ask an administrator for access if you believe this to be in error.', 'response')

	if str(interaction.user.id) not in config['discord']['emojis']:
		return await handleError(interaction, 'You do not have an emoji set. Please use /set_emoji to set your own emoji.', 'response')

	emoji = config['discord']['emojis'][str(interaction.user.id)].encode('utf-16', 'surrogatepass').decode('utf-16')
	urlType = ''

	regex = r"\?(?:\w+=\w+&)*(?:ex|hm)=[^&]+&?|(?:\w+=\w+&)*(?:size|name)=[^&]+&?"
	url = re.sub(regex, '', url)

	if url.startswith('https://tenor.com/view/'): urlType = 'tenor'
	elif url.startswith('https://giphy.com/gifs/'): urlType = 'giphy'
	elif url.endswith('.gif'): urlType = 'gif'
	else: return await handleError(interaction, 'The URL provided is not supported by the bot.\nCurrently, only the following links are supported:\n- Tenor\n- Giphy\n- URLs that end in .gif (note: please remove any additional parameters in the URL, or else this won\'t function properly.)', 'response')

	await parseURL(interaction, url, caption, urlType, alt_text, emoji)

@tweet.error
async def tweet_error(interaction: discord.Interaction, error):
	await handleError(interaction, f'An error has occurred.\n\n```{error}```', 'edit')


@bot.tree.context_menu(name='Fetch URL')
async def fetch_url(interaction: discord.Interaction, message: discord.Message):
	attachments = ''
	split_text = message.content.split()
	regex = r"\?(?:\w+=\w+&)*(?:ex|hm)=[^&]+&?|(?:\w+=\w+&)*(?:size|name)=[^&]+&?"

	# iterate through the split message text and check for links
	for text in split_text.copy():
		if ('https://tenor' in text or 'https://giphy' in text or 'https://media.tenor' or text.endswith('.gif') or ('https://' in text and 'discord' in text)) == True:
			attachments += f'<{re.sub(regex, "", text)}>\n'
			split_text.remove(text)

	# iterate through attachmentss
	if message.attachments:
		for attachment in message.attachments:
			attachments += f'<{re.sub(regex, "", attachment.url)}>\n'

	# iterate through embeds
	if message.embeds:
		for embed in message.embeds:
			if embed.image:
				attachments += f'<{re.sub(regex, "", embed.image.url)}>\n'

	# return final result
	if attachments == '':
		return await handleError(interaction, 'No URLs were found in the message.', 'response')
	else:
		await interaction.response.send_message(content=attachments)


# Admin commands
@bot.tree.command(name = 'set_emoji')
@discord.app_commands.describe(user = 'The user you wish to set the emoji for', emoji = 'The emoji you want to append to their posts')
async def set_emoji(interaction: discord.Interaction, user: Union[discord.User, discord.Member], emoji: str):
	config = fetch_data()

	bot_info = await bot.application_info()
	owner_id = bot_info.owner.id

	if interaction.user.id != owner_id:
		return await handleError(interaction, 'You do not have permission to run this command.', 'response')

	config['discord']['emojis'][str(user.id)] = emoji
	write_data(config)

	embed = discord.Embed(title = 'Success', description = f'<@{user.id}>\'s emoji has been set to {emoji}', color = discord.Color.from_str(config['discord']['embed_colors']['success']))
	await interaction.response.send_message(embed = embed)

@bot.tree.command(name = 'add_user')
@discord.app_commands.describe(user = 'The user you wish to add to the list of permitted users')
async def add_user(interaction: discord.Interaction, user: Union[discord.User, discord.Member]):
	config = fetch_data()

	bot_info = await bot.application_info()
	owner_id = bot_info.owner.id

	if interaction.user.id != owner_id:
		return await handleError(interaction, 'You do not have permission to run this command.', 'response')

	if user.id not in config['discord']['authed_users']:
		config['discord']['authed_users'].append(user.id)
		write_data(config)

		embed = discord.Embed(title = 'Success', description = f'<@{user.id}> has been added to the list of authenticated users.', color = discord.Color.from_str(config['discord']['embed_colors']['success']))
		await interaction.response.send_message(embed = embed)
	else:
		return await handleError(interaction, f'<@{user.id}> is already in the list of authenticated users.', 'response')


@bot.tree.command(name = 'remove_user')
@discord.app_commands.describe(user = 'The user you wish to remove from the list of permitted users')
async def remove_user(interaction: discord.Interaction, user: Union[discord.User, discord.Member]):
	config = fetch_data()

	bot_info = await bot.application_info()
	owner_id = bot_info.owner.id

	if interaction.user.id != owner_id:
		return await handleError(interaction, 'You do not have permission to run this command.', 'response')

	if user.id in config['discord']['authed_users']:
		config['discord']['authed_users'].remove(user.id)
		write_data(config)

		embed = discord.Embed(title = 'Success', description = f'<@{user.id}> has been removed from the list of authenticated users.', color = discord.Color.from_str(config['discord']['embed_colors']['success']))
		await interaction.response.send_message(embed = embed)
	else:
		return await handleError(interaction, f'<@{user.id}> is not in the list of authenticated users.', 'response')


log.info('Logging in to discord')
try:
	bot.run(token)
except:
	log.error(f'An error occured when logging in to Discord\n{traceback.format_exc()}')