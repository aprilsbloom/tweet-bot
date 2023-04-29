# Tweet Bot

This repository serves as the source code for the bot I use to post on [@gifkitties](https://twitter.com/gifkitties), an account dedicated to posting cat gifs.
It was created to simplify the purpose of posting to the account by creating a Discord bot, as well as to learn how to use the Twitter API.

## Features

- Tweet gifs from Discord, simplifying the process and linking the source of the gif in the tweet.
- Currently, the bot is only able to tweet gifs from Tenor, Giphy & raw links, but I plan to add more sources in the future if I find any.

## Setup

Run `pip install -r requirements.txt` to install the required dependencies.

Then, run `main.py`. It will create a file by the name of `config.json`, which you will need to fill out with your own API keys.

Once you have filled out `config.json`, run `main.py` again - it will then launch the bot.
