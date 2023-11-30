import re
import discord
from discord.ext import commands
from typing import Optional, Union
from httpx import AsyncClient
from cogs.queue._views import AuthedQueueViewBasic
from utils.general import is_user_authorized, create_embed, handle_base_response, error_response
from utils.config import load_config, write_config
from utils.constants import BASE_HEADERS, CATBOX_URL, CLEAN_URL_REGEX, FILESIZE_LIMIT_TWITTER, TENOR_REGEX



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
		client = AsyncClient()
		config = load_config()
		bot_info = await self.bot.application_info()

		# Check if the user is authorized to run this command
		if not is_user_authorized(interaction.user.id, bot_info):
			return await interaction.response.send_message(
				embed = create_embed(
					"Error",
					"You do not have permission to run this command.\nPlease ask an administrator for access if you believe this to be in error.",
					'error'
				),
				ephemeral = True
			)

		# Check to see if the user has an emoji set (required to post)
		if str(interaction.user.id) not in config["discord"]["emojis"]:
			return await interaction.response.send_message(
				embed = create_embed(
					"Error",
					"You do not have an emoji set.\nPlease set an emoji with `/emoji set `.",
					'error'
				),
				ephemeral = True
			)

		# Decode the users emoji into an acceptable format
		emoji = (
			config["discord"]["emojis"][str(interaction.user.id)]
			.encode("utf-16", "surrogatepass")
			.decode("utf-16")
		)

		# Return a response in <= 3 seconds to prevent the command from erroring
		await handle_base_response(
			interaction = interaction,
			config = config,
			responseType = "info",
			content = "Determining if the gif is valid...",
		)

		# Determine the real url of the gif, depending
		url = await self.find_real_url(url)
		if not url:
			return await handle_base_response(
				interaction = interaction,
				config = config,
				responseType = "error",
				content = "Either a GIF was unable to be found from the link provided, or you have provided a link that is currently not supported.\nPlease note that at the moment we only support Tenor, Giphy, and any other URL that ends in .gif.",
			)

		# Check to see if the gif is already in the queue
		for post in config['queue']:
			if post["original_url"] == url:
				return await handle_base_response(
					interaction = interaction,
					config = config,
					responseType = "error",
					content = "The URL you entered is already in the queue.",
				)

		# Check to see if the gif is too large
		is_small_enough = await self.check_file_size(url)
		if not is_small_enough:
			return await handle_base_response(
				interaction = interaction,
				config = config,
				responseType = "error",
				content = "The gif you uploaded is too large. Please compress your file to below 15MB in size, and try again.",
			)

		# If userhash field is not in config, return error
		# This is more just a courtesy thing to the owner of the service :P
		# Don't want to accidentally spam them with requests and them have no idea who it is
		if not config["userhash"]:
			return await handle_base_response(
				interaction = interaction,
				config = config,
				responseType = "error",
				content = "The bot owner has not set the `user_hash` property for uploads to [catbox](https://catbox.moe).",
			)

		# Upload the file to catbox.moe
		res = await client.post(
			url = CATBOX_URL,
			headers = BASE_HEADERS,
			data = {
				"reqtype": "urlupload",
				"userhash": config["userhash"],
				"url": url,
			}
		)

		# Check to see if the upload was successful
		if res.status_code != 200 or "Something went wrong" in res.text:
			return await handle_base_response(
				interaction = interaction,
				config = config,
				responseType = "error",
				content = "An error occurred while uploading your gif to catbox.moe. Please try again later.",
			)

		# Add the post to the queue
		post = {
			"original_url": url,
			"catbox_url": res.text,
			"author": interaction.user.id,
			"emoji": emoji,
			"caption": caption,
			"alt_text": alt_text,
		}
		config['queue'].append(post)
		write_config(config)

		# Return a success message
		embed = create_embed(
			"Success",
			"Your gif has been added to the queue.",
			"success",
		)

		if caption:
			embed.add_field(name = "Caption", value = caption, inline = False)

		embed.add_field(name = "Alt Text", value = alt_text, inline = False)
		embed.add_field(name = "Gif URL", value = res.text, inline = False)
		embed.set_image(url = url)

		if interaction.response.is_done():
			await interaction.edit_original_response(embed = embed, view = AuthedQueueViewBasic(post, bot_info))
		else:
			await interaction.response.send_message(embed = embed, view = AuthedQueueViewBasic(post, bot_info))

		await client.aclose()


	@tweet.error
	async def tweet_error(self, interaction: discord.Interaction, error):
		await error_response(interaction, error, '/tweet')


	async def find_real_url(self, url: str) -> Union[str, None]:
		client = AsyncClient()
		clean_url = re.sub(CLEAN_URL_REGEX, "", url)

		if clean_url.startswith("https://tenor.com/view"):
			res = await client.get(url)

			await client.aclose()
			return re.search(TENOR_REGEX, res.text).group(0)
		elif clean_url.startswith("https://giphy.com/gifs/"):
			res = await client.get(url)
			tmp_url = res.text.split('property = "og:image" content = "')[1].split('"')[0]

			await client.aclose()
			return None if tmp_url == "https://giphy.com/static/img/giphy-be-animated-logo.gif" else tmp_url
		elif clean_url.endswith('.gif'):
			await client.aclose()
			return url
		else:
			await client.aclose()
			return None

	async def check_file_size(self, url: str) -> bool:
		client = AsyncClient()
		res = await client.head(url, headers = BASE_HEADERS, timeout = 30)
		content_length_header = None

		for header in res.headers:
			if header.lower() == "content-length":
				content_length_header = header
				break

		if not content_length_header:
			new_res = await client.get(url, headers = BASE_HEADERS, timeout = 30)
			await client.aclose()
			return True if int(len(new_res.content)) <= FILESIZE_LIMIT_TWITTER else False

		await client.aclose()
		return True if int(res.headers[content_length_header]) <= FILESIZE_LIMIT_TWITTER else False




async def setup(bot: commands.Bot):
	await bot.add_cog(Tweet(bot))