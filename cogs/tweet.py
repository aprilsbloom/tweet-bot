import discord
from discord.ext import commands
from typing import Optional
from urllib.parse import urlparse
from httpx import AsyncClient
from bs4 import BeautifulSoup, Tag


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
		real_url = await self.find_real_url(url)
		if not real_url:
			await interaction.response.send_message("Invalid link.")
			return

		await interaction.response.send_message(f'<{real_url}>')


	async def find_real_url(self, url: str) -> Optional[str]:
		client = AsyncClient()
		parsed_url = urlparse(url)

		if parsed_url.path.endswith(".gif"):
			exists = await client.head(url)
			await client.aclose()
			return url if exists.status_code == 200 else None

		# tenor
		if (
			parsed_url.netloc == "tenor.com" and
			parsed_url.path.startswith("/view")
		):
			pass

		# giphy
		if (
			parsed_url.netloc == "giphy.com" and
			parsed_url.path.startswith("/gifs")
		):
			res = await client.get(url)

			# non-ok status
			if res.status_code != 200:
				await client.aclose()
				return None

			# parse the og:image meta tag for the raw gif url
			soup = BeautifulSoup(res.text, 'html.parser')
			elem: Tag = soup.find("meta", property = "og:image") # type: ignore
			if elem:
				await client.aclose()

				# sanity check for removed/404'd gifs
				url = elem.attrs["content"]
				if url == "https://giphy.com/static/img/giphy-be-animated-logo.gif":
					return None

				return url

		return None

async def setup(bot: commands.Bot):
	await bot.add_cog(Tweet(bot))