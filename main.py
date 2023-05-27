# <-- Imports -->
import os
import traceback
import filetype
import re
import discord
import tweepy
import json
import requests
from discord.ext import commands, tasks


# <-- Functions -->
async def parseURL(interaction, url, caption, urlType, alt_text):
    gifURL = ''

    try:
        if urlType == 'gif':
            gifURL = url
        elif urlType == 'tenor':
            gifURL = findTenorURL(url)
        elif urlType == 'giphy':
            gifURL = findGiphyURL(url)
            if gifURL == 'https://giphy.com/static/img/giphy-be-animated-logo.gif':
                return await handleError(interaction=interaction, errorType='response', errorText='Unable to find the gif from the link provided.')
    except:
        return await handleError(interaction=interaction, errorType='response', errorText=f'An error has occurred.\n\n```{traceback.format_exc()}```')

    r = requests.get(gifURL, stream = True)
    if r.status_code == 200:
        with open('gif', 'wb') as f:
            f.write(r.content)

        kind = filetype.guess('gif')
        if kind is None or kind.extension != 'gif':
            return await handleError(interaction=interaction, errorType='response', errorText='The file provided is not a gif..')

        embed = discord.Embed(title = 'Info', description = 'Downloaded gif.', color = 0x3498DB)
        await interaction.response.send_message(embed = embed)

        await postGif(interaction, url, gifURL, caption, alt_text)
    else:
        return await handleError(interaction=interaction, errorType='response', errorText='Unable to download gif.')


async def postGif(interaction, url, rawURL, caption, alt_text):
    try:
        gif = v1.chunked_upload(filename='gif', media_category="tweet_gif").media_id_string

        if alt_text != '':
            v1.create_media_metadata(media_id=gif, alt_text=alt_text)

        if os.path.exists('gif') and os.path.isfile('gif'):
            os.remove('gif')

        # post gif
        try:
            post = v2.create_tweet(text=caption, media_ids=[gif])
            link = v2.create_tweet(text=url, in_reply_to_tweet_id=post[0]['id'])

            embed = discord.Embed(title='Success', description=f'[View Tweet](https://twitter.com/gifkitties/status/{post[0]["id"]})', color=discord.Color.green())
            embed.set_image(url=rawURL)
            await interaction.edit_original_response(embed=embed)

        except:
            return await handleError(interaction=interaction, errorType='edit', errorText=f'An error has occured when attempting to post the tweet.\n\n```{traceback.format_exc()}```')
    except:
        errorMsg = traceback.format_exc()

        if 'File size exceeds 15728640 bytes.' in errorMsg:
            errorMsg = 'The gif provided is over 15MB.\nPlease try again with a smaller gif, or compress the file.'

        return await handleError(interaction=interaction, errorText=f'An error has occurred.\n\n```{errorMsg}```')


# Regex to find the raw URL on tenor
def findTenorURL(s):
    r = requests.get(s)
    regex = r'(?i)\b((https?://media[.]tenor[.]com/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))[.]gif)'
    return re.findall(regex, r.text)[0][0]


# Function to find the raw URL on giphy
def findGiphyURL(s):
    r = requests.get(s)
    return r.text.split('<meta property="og:image" content="')[1].split('"')[0]

def fetch_data():
    temp_config = {
        "discord": {
            "token": ""
        },
        "twitter": {
            "consumer_key": "",
            "consumer_secret": "",
            "access_token": "",
            "access_token_secret": "",
            "bearer_token": ""
        }
    }

    try:
        with open('config.json', 'r', encoding='utf8') as file:
            temp_config.update(json.load(file))
            write_data(temp_config)
            return temp_config

    except (FileNotFoundError, json.decoder.JSONDecodeError):
        print(f'{Colors.red}[!]{Colors.reset} Config file not found! Creating one')
        write_data(temp_config)
        os._exit(0)


def write_data(data):
    with open('config.json', 'w', encoding='utf8') as file:
        file.write(json.dumps(data, indent=4))


# Function to handle errors, prevents me from having to write the same code over and over again
async def handleError(**args):
    if os.path.exists('gif') and os.path.isfile('gif'):
        try:
            os.remove('gif')
        except:
            pass

    interaction = args.get('interaction')
    errorType = args.get('errorType', 'edit')
    errorText = args.get('errorText', 'An error has occurred.')

    embed = discord.Embed(title = 'Error', description = errorText, color = 0xff0000)

    if errorType == 'edit':
        await interaction.edit_original_response(embed = embed)
    elif errorType == 'response':
        await interaction.response.send_message(embed = embed)


# <-- Classes -->
class Colors:
    green = "\033[92m"
    red = "\033[91m"
    gray = "\033[90m"
    reset = "\033[0m"


# <-- Variables -->
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


# <-- Events -->
@bot.tree.command(name='tweet')
@discord.app_commands.describe(url = 'The URL of the gif you want to tweet.', caption = 'The caption you want to add to the tweet. (Optional)')
async def tweet(interaction: discord.Interaction, url: str, caption: str = '', alt_text: str = ''):
    if url.startswith('https://tenor.com/view/'):
        await parseURL(interaction, url, caption, 'tenor', alt_text)
    elif url.startswith('https://giphy.com/gifs/'):
        await parseURL(interaction, url, caption, 'giphy', alt_text)
    elif url.endswith('.gif'):
        await parseURL(interaction, url, caption, 'gif', alt_text)
    else:
        return await handleError(interaction=interaction, errorType='response', errorText='Invalid URL provided.\nThe bot currently supports the following sites:```\n• Tenor\n• Giphy\n• Direct links to a gif (ending with .gif)```')


@bot.event
async def on_ready():
    os.system('cls' if os.name == 'nt' else 'clear')
    print(f'{Colors.green}[+]{Colors.reset} Logged in as {bot.user}')

    try:
        synced = await bot.tree.sync()
        print(f'{Colors.green}[+]{Colors.reset} Synced {len(synced)} commands')
    except Exception:
        print(f'{Colors.red}[!]{Colors.reset} An error has occurred while syncing commands.\n{traceback.format_exc()}')
        return


# <-- Main -->
bot.run(token)