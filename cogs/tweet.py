from enum import Enum
import discord
from discord.ext import commands
from typing import Optional
from urllib.parse import urlparse
from httpx import AsyncClient, TimeoutException
from bs4 import BeautifulSoup

from globals import cfg, headers
from utils.config import Post, save_cfg

class Error(Enum):
	NonOk = 1
	CouldntFind = 2
	FailedUpload = 3
	Timeout = 4
	Unknown = 5

class Tweet(commands.Cog):
	def __init__(self, bot: commands.Bot):
		self.bot = bot

	@discord.app_commands.command(name = "tweet", description = "Post a tweet")
	@discord.app_commands.describe(
		url = "The URL of the gif you want to tweet (please remove any additional text in the URL)",
		alt_text = "The alt text of the tweet (please be as informative as possible)",
		caption = "The caption of the tweet",
	)
	async def tweet(
		self,
		interaction: discord.Interaction,
		url: str,
		alt_text: str,
		caption: Optional[str] = "",
	):
		# defer the response
		await interaction.response.defer()

		# remove any query parameters from the URL and check if it's in queue already
		parsed_user_url = urlparse(url)
		cleaned_user_url = f"{parsed_user_url.scheme}://{parsed_user_url.netloc}{parsed_user_url.path}"
		for post in cfg["queue"]:
			parsed_post_url = urlparse(post["raw_url"])
			cleaned_post_url = f"{parsed_post_url.scheme}://{parsed_post_url.netloc}{parsed_post_url.path}"

			if cleaned_post_url == cleaned_user_url:
				embed = discord.Embed(
					title = "Error",
					description = "This gif is already in the queue.",
					color = discord.Color.red(),
				)

				await interaction.edit_original_response(embed = embed)
				return

		# find real url of the gif (links can be behind tenor or giphy, or just a direct link)
		real_url = await self.find_real_url(url)
		if isinstance(real_url, Error):
			embed = discord.Embed(
				title = "Error",
				description = "Please try again.",
				color = discord.Color.red(),
			)

			if real_url == Error.NonOk:
				embed.description = "Failed to fetch the gif."
			elif real_url == Error.CouldntFind:
				embed.description = "Couldn't find the gif in the URL you provided."
			elif real_url == Error.Timeout:
				embed.description = "The request to fetch the gif timed out. Please try again."
			elif real_url == Error.Unknown:
				embed.description = "An unknown error occurred while fetching the gif."

			await interaction.edit_original_response(embed = embed)
			return

		# upload to catbox
		catbox_url = await self.upload_to_catbox(real_url)
		if isinstance(catbox_url, Error):
			embed = discord.Embed(
				title = "Error",
				description = "Please try again.",
				color = discord.Color.red(),
			)

			if catbox_url == Error.NonOk or catbox_url == Error.FailedUpload:
				embed.description = "Failed to upload to Catbox."
			elif catbox_url == Error.Timeout:
				embed.description = "The request to upload to Catbox timed out. Please try again."
			elif catbox_url == Error.Unknown:
				embed.description = "An unknown error occurred while uploading to Catbox."

			await interaction.edit_original_response(embed = embed)
			return

		# create post object and add to config
		post: Post = {
			"author_id": interaction.user.id,
			"alt_text": alt_text,
			"caption": caption,
			"catbox_url": catbox_url,
			"raw_url": real_url,
		}

		cfg["queue"].append(post)
		save_cfg(cfg)

		# send success message
		embed = discord.Embed(
			title = "Tweet added to queue!",
			color = discord.Color.green(),
		)

		embed.add_field(name = "URL", value = catbox_url, inline = False)
		embed.set_image(url = real_url)

		if caption:
			embed.add_field(name = "Caption", value = caption, inline = False)

		embed.add_field(name = "Alt Text", value = alt_text, inline = False)

		await interaction.edit_original_response(embed = embed)

	async def find_real_url(self, url: str) -> Error | str:
		client = AsyncClient()
		parsed_url = urlparse(url)

		if parsed_url.path.endswith(".gif"):
			res = await client.head(
				url,
				headers = {
					"Accept": "image/gif",
				}
			)

			await client.aclose()
			if res.status_code != 200:
				return Error.NonOk

			return url

		# tenor
		if (
			parsed_url.netloc == "tenor.com" and
			parsed_url.path.startswith("/view")
		):
			res = await client.get(url)
			await client.aclose()

			if res.status_code != 200:
				return Error.NonOk

			soup = BeautifulSoup(res.text, 'html.parser')
			elem = soup.select_one("#single-gif-container .Gif > img") # type: ignore
			if elem:
				return elem.attrs["src"]
			else:
				return Error.CouldntFind

		# giphy
		elif (
			parsed_url.netloc == "giphy.com" and
			parsed_url.path.startswith("/gifs")
		):
			res = await client.get(url)
			await client.aclose()

			if res.status_code != 200:
				return Error.NonOk

			# parse the og:image meta tag for the raw gif url
			soup = BeautifulSoup(res.text, 'html.parser')
			elem = soup.select_one("meta[property=og:image]")

			if elem:
				# sanity check for removed/404'd gifs
				url = elem.attrs["content"]
				if url == "https://giphy.com/static/img/giphy-be-animated-logo.gif":
					return Error.CouldntFind

				return url
			else:
				return Error.CouldntFind

		return Error.CouldntFind

	async def upload_to_catbox(self, url: str) -> Error | str:
		client = AsyncClient()

		try:
			res = await client.post(
				url = "https://catbox.moe/user/api.php",
				headers = headers,
				data = {
					"reqtype": "urlupload",
					"userhash": cfg["user_hash"],
					"url": url,
				}
			)
		except TimeoutException:
			await client.aclose()
			return Error.Timeout
		except Exception:
			await client.aclose()
			return Error.Unknown

		# Check to see if the upload was successful
		await client.aclose()
		if res.status_code != 200:
			return Error.NonOk

		if "Something went wrong" in res.text:
			return Error.FailedUpload

		return res.text

async def setup(bot: commands.Bot):
	await bot.add_cog(Tweet(bot))