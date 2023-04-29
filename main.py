# <-- Imports -->
import os
import traceback
import filetype
import re
import discord
import tweepy
import json
import requests
from requests_oauthlib import OAuth1
from discord.ext import commands


# <-- Functions -->
async def parseURL(interaction, url, caption, urlType):
    gifURL = ''

    try:
        if urlType == 'gif':
            gifURL = url
        elif urlType == 'tenor':
            gifURL = findTenorURL(url)
        elif urlType == 'giphy':
            gifURL = findGiphyURL(url)
            if gifURL == 'https://giphy.com/static/img/giphy-be-animated-logo.gif':
                return await handleError(interaction=interaction, errorType='response', errorText='Unable to find the gif from the link provided. Please try again.')
    except:
        return await handleError(interaction=interaction, errorType='response', errorText=f'An error has occurred. Please try again.\n\n```{traceback.format_exc()}```')

    r = requests.get(gifURL, stream = True)
    if r.status_code == 200:
        with open('gif', 'wb') as f:
            f.write(r.content)

        kind = filetype.guess('gif')
        if kind is None or kind.extension != 'gif':
            return await handleError(interaction=interaction, errorType='response', errorText='The file provided is not a gif. Please try again.')

        embed = discord.Embed(title = 'Info', description = 'Downloaded gif.', color = 0x3498DB)
        await interaction.response.send_message(embed = embed)

        await postGif(interaction, url, gifURL, caption)
    else:
        return await handleError(interaction=interaction, errorType='response', errorText='Unable to download gif. Please try again.')


async def postGif(interaction, url, rawURL, caption):
    newCaption = f'{caption}\n\n{url}' if caption != '' else url
    try:
        gif = api.chunked_upload(filename='gif', media_category="tweet_gif").media_id_string
        if os.path.exists('gif') and os.path.isfile('gif'):
            os.remove('gif')

        r = requests.post(
            url = 'https://api.twitter.com/2/tweets',
            json = {
                "text": newCaption,
                "media": {
                    "media_ids": [gif]
                }
            },
            auth = OAuth
        )

        if r.status_code == 201:
            embed = discord.Embed(title = 'Success', description = f'[View tweet](https://twitter.com/gifkitties/status/{r.json()["data"]["id"]})', color = 0x00ff00)
            embed.set_image(url = rawURL)
            await interaction.edit_original_response(embed = embed)
        else:
            return await handleError(interaction=interaction, errorType='response', errorText='An error has occured when attempting to post the tweet. Please try again.\n\n```{r.json()}```')
    except:
        if os.path.exists('gif') and os.path.isfile('gif'):
            os.remove('gif')

        return await handleError(interaction=interaction, errorText=f'An error has occurred. Please try again.\n\n```{traceback.format_exc()}```')


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
            "access_token_secret": ""
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
        os.remove('gif')

    interaction = args.get('interaction')
    errorType = args.get('errorType', 'edit')
    errorText = args.get('errorText', 'An error has occurred. Please try again.')

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

OAuth = OAuth1(CONSUMER_KEY, CONSUMER_SECRET, ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
tweepy_auth = tweepy.OAuth1UserHandler(CONSUMER_KEY, CONSUMER_SECRET, ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
api = tweepy.API(tweepy_auth, wait_on_rate_limit=True)


# <-- Events -->
@bot.tree.command(name='tweet')
@discord.app_commands.describe(url = 'The URL of the gif you want to tweet.', caption = 'The caption you want to add to the tweet. (Optional)')
async def tweet(interaction: discord.Interaction, url: str, caption: str = ''):
    if url.startswith('https://tenor.com/view/'):
        await parseURL(interaction, url, caption, 'tenor')
    elif url.startswith('https://giphy.com/gifs/'):
        await parseURL(interaction, url, caption, 'giphy')
    elif url.endswith('.gif'):
        await parseURL(interaction, url, caption, 'gif')
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