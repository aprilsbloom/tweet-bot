import os
import traceback
from typing import Union
import filetype
import re
import discord
import tweepy
import requests
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
# CONSUMER_KEY = config['twitter']['consumer_key']
# CONSUMER_SECRET = config['twitter']['consumer_secret']
# ACCESS_TOKEN = config['twitter']['access_token']
# ACCESS_TOKEN_SECRET = config['twitter']['access_token_secret']
# BEARER_TOKEN = config['twitter']['bearer_token']

# tweepy_auth = tweepy.OAuth1UserHandler(CONSUMER_KEY, CONSUMER_SECRET, ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
# v1 = tweepy.API(tweepy_auth, wait_on_rate_limit=True)
# v2 = tweepy.Client(consumer_key=CONSUMER_KEY, consumer_secret=CONSUMER_SECRET, access_token=ACCESS_TOKEN, access_token_secret=ACCESS_TOKEN_SECRET, bearer_token=BEARER_TOKEN, wait_on_rate_limit=True)

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

async def parseURL(interaction, url, caption, urlType, alt_text):
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
                return await handleError(interaction=interaction, errorType='response', errorText='Unable to find the gif from the link provided.')
    except:
        return await handleError(interaction=interaction, errorType='response', errorText=f'An error has occurred.\n\n```{traceback.format_exc()}```')

    r = requests.get(gifURL)
    if r.status_code == 200:
        with open('gif', 'wb') as f:
            f.write(r.content)

        kind = filetype.guess('gif')
        if kind is None or kind.extension != 'gif':
            return await handleError(interaction=interaction, errorType='response', errorText='The file provided is not a gif.')

        embed = discord.Embed(title = 'Info', description = 'Downloaded gif.', color = 0x3498DB)
        await interaction.response.send_message(embed = embed)

        await postGif(interaction, url, caption, alt_text)
    else:
        return await handleError(interaction=interaction, errorType='response', errorText='Unable to download gif.')

async def postGif(interaction, url, caption, alt_text):
    try:
        gif_res = v1.chunked_upload(filename='gif', media_category="tweet_gif").media_id_string

        if alt_text != '':
            v1.create_media_metadata(media_id=gif_res, alt_text=alt_text)

        if os.path.exists('gif') and os.path.isfile('gif'):
            os.remove('gif')

        # post gif
        try:
            post = v2.create_tweet(text=caption, media_ids=[gif_res])
            v2.create_tweet(text=url, in_reply_to_tweet_id=post[0]['id'])

            embed = discord.Embed(title='Success', description=f'[View Tweet](https://twitter.com/gifkitties/status/{post[0]["id"]})', color=discord.Color.green())
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
    embed = discord.Embed(title = 'Error', description = errorText, color = 0xff0000)

    if errorType == 'response':
        await interaction.response.send_message(embed=embed)
    elif errorType == 'edit':
        await interaction.edit_original_response(embed = embed)


@bot.tree.command(name='set_emoji')
@discord.app_commands.describe(emoji = 'The emoji you want to append to your own posts')
async def set_emoji(interaction: discord.Interaction, emoji: str):
    config = fetch_data()

    if interaction.author.id not in config['discord']['authed_users']:
        return handleError(interaction, 'You do not have permission to run this command. Please ask an administrator for access if you believe this to be in error')

    config['discord']['emojis'][str(interaction.author.id)] = emoji
    write_data(config)

    embed = discord.Embed(title = 'Success', description = f'Your emoji has been set to {emoji}')
    await interaction.response.send_message(embed = embed)

@bot.tree.command(name = 'add_user')
@discord.app_commands.describe(user = 'The user you wish to add to the list of permitted users')
async def add_user(interaction: discord.Interaction, user: Union[discord.User, discord.Member]):
    config = fetch_data()
    if user.id not in config['discord']['authed_users']:
        config['discord']['authed_users'].append(user.id)
        write_data(config)

        embed = discord.Embed(title = 'Success', description = f'<@{user.id}> has been added to the list of authenticated users.')
        await interaction.response.send_message(embed = embed)

@bot.tree.command(name = 'remove_user')
@discord.app_commands.describe(user = 'The user you wish to remove from the list of permitted users')
async def remove_user(interaction: discord.Interaction, user: Union[discord.User, discord.Member]):
    config = fetch_data()
    if user.id in config['discord']['authed_users']:
        config['discord']['authed_users'].remove(user.id)
        write_data(config)

        embed = discord.Embed(title = 'Success', description = f'<@{user.id}> has been removed from the list of authenticated users.')
        await interaction.response.send_message(embed = embed)
    else:
        return handleError(interaction, f'<@{user.id}> is not in the list of authenticated users.')

@bot.tree.command(name = 'tweet')
@discord.app_commands.describe(url = 'The gif URL you want to tweet', caption = 'The caption of the tweet', alt_text = 'The alt text of the tweet')
async def tweet(interaction: discord.Interaction, url: str, caption: str = '', alt_text: str = ''):
    if url.startswith('https://tenor.com/view/'):
        await parseURL(interaction, url, caption, 'tenor', alt_text)
    elif url.startswith('https://giphy.com/gifs/'):
        await parseURL(interaction, url, caption, 'giphy', alt_text)
    elif url.endswith('.gif'):
        await parseURL(interaction, url, caption, 'gif', alt_text)

@tweet.error
async def tweet_error(interaction: discord.Interaction, error):
    await handleError(interaction, errorText=f'An error has occurred.\n\n```{traceback.format_exc()}```')

@bot.tree.context_menu(name='Fetch URL')
async def fetch_url(interaction: discord.Interaction, message: discord.Message):
    attachments = ''
    for text in message.content.split():
        if 'https://tenor' in text or 'https://giphy' in text or 'https://media.tenor' or text.endswith('.gif'):
            attachments += f'<{text}>\n'

    if message.attachments:
        for attachment in message.attachments:
            attachments += f'<{attachment.url}>\n'

    await interaction.response.send_message(content=attachments)


log.info('Logging in to discord')
try:
    bot.run(token, log_handler=None)
except:
    log.error(f'An error occured when logging in to Discord\n{traceback.format_exc()}')