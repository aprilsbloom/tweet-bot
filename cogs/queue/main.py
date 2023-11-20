import discord
import traceback
from discord.ext import commands
from cogs.queue._views import AuthedQueueViewBasic, AuthedQueueViewExtended
from utils.general import handleResponse, is_user_authorized
from utils.logger import Logger
from utils.config import load_config, write_config

log = Logger()

class Queue(commands.Cog):
	def __init__(self, bot: commands.Bot):
		self.bot = bot

	group = discord.app_commands.Group(
		name = 'queue',
		description = 'Commands to manage the post queue.'
	)


	@group.command(
		name = 'view',
		description = 'View the post queue.',
	)
	async def queue_view(self, interaction: discord.Interaction):
		config = load_config()
		bot_info = await self.bot.application_info()
		queue_length = len(config['twitter']['queue'])

		# if queue is empty, return
		if queue_length == 0:
			return await handleResponse(
				interaction = interaction,
				config = config,
				responseType = 'info',
				content = 'The queue is empty.'
			)

		# if there is only one post in the queue, return it & the basic queue view
		if queue_length == 1:
			post = config["twitter"]["queue"][0]
			embed = discord.Embed(title = "Queue list")

			# add caption field if present
			if post["caption"] != "":
				embed.add_field(name = "Caption", value = post["caption"], inline = False)

			# add alt text field (required)
			embed.add_field(name = "Alt text", value = post["alt_text"], inline = False)

			author_user = post["author"]
			author_emoji = post["emoji"]

			embed.add_field(
				name = "Author",
				value = f"**<@{author_user}>** - {author_emoji}",
				inline = False,
			)
			embed.add_field(name = "Gif URL", value = post["catbox_url"])
			embed.set_image(url = post["catbox_url"])
			embed.set_footer(text = f"Post {queue_length} / {queue_length}")

			if interaction.response.is_done():
				return await interaction.edit_original_response(embed = embed, view=AuthedQueueViewBasic(post, bot_info))
			else:
				return await interaction.response.send_message(embed = embed, view=AuthedQueueViewBasic(post, bot_info))

		# if there are multiple posts in the queue, return an array of posts & the extended view
		if queue_length > 1:
			embeds = []

			for count, post in enumerate(config["twitter"]["queue"], start=1):
				embed = discord.Embed(title = "Queue list")

				if post["caption"] != "":
					embed.add_field(name = "Caption", value = post["caption"], inline = False)

				embed.add_field(name = "Alt text", value = post["alt_text"], inline = False)

				author_user = post["author"]
				author_emoji = post["emoji"]

				embed.add_field(
					name = "Author",
					value = f"**<@{author_user}>** - {author_emoji}",
					inline = False,
				)
				embed.add_field(name = "Gif URL", value = post["catbox_url"])
				embed.set_image(url = post["catbox_url"])
				embed.set_footer(text = f"Post {count} / {queue_length}")

				embeds.append({
					"embed": embed,
					"post": post
				})

			if interaction.response.is_done():
				return await interaction.edit_original_response(embed = embeds[0]['embed'], view=AuthedQueueViewExtended(embeds, bot_info))
			else:
				return await interaction.response.send_message(embed = embeds[0]['embed'], view=AuthedQueueViewExtended(embeds, bot_info))

	@queue_view.error
	async def queue_view_error(self, interaction: discord.Interaction, error):
		config = load_config()
		log.error(f"An error has occurred while running /queue view{error}")
		return await handleResponse(
			interaction = interaction,
			config = config,
			content = f'An unknown error has occurred:\n```{error}\n```',
			responseType = 'error'
		)

	@group.command(
		name = 'remove',
		description = "Remove an item from the queue"
	)
	async def queue_remove(self, interaction: discord.Interaction, url: str):
		config = load_config()
		post = config["twitter"]["queue"][0]
		bot_info = await self.bot.application_info()

		queue_length = len(config["twitter"]["queue"])
		if queue_length == 0:
			return await handleResponse(
				interaction = interaction,
				config = config,
				content = "The tweet queue is empty. Please try again later",
				responseType = "error",
			)

		if not is_user_authorized(interaction.user.id, self.bot_info):
			return await handleResponse(
				interaction = interaction,
				config = config,
				content = "You do not have permission to run this command.\nPlease ask an administrator for access if you believe this to be in error.",
				responseType = "error",
			)

		if not url:
			return await handleResponse(
				interaction = interaction,
				config = config,
				content = "You have not entered a URL to remove from the queue.",
				responseType = "error",
			)

		# Finding the GIF within the queue and removing it
		foundGif = False
		for post in config.copy()["twitter"]["queue"]:
			if post["catbox_url"] == url:
				config["twitter"]["queue"].remove(post)
				write_config(config)
				foundGif = True

		if foundGif:
			return await handleResponse(
				interaction=interaction,
				config=config,
				content="The URL you have entered has been successfully removed from the queue",
				responseType="success",
			)
		else:
			await handleResponse(
				interaction=interaction,
				config=config,
				content="The URL you have entered was not found in the queue.",
				responseType="error",
			)

	@queue_remove.error
	async def queue_remove_error(self, interaction: discord.Interaction, error):
		config = load_config()
		log.error(f"An error has occurred while running /queue remove{error}")
		return await handleResponse(
			interaction = interaction,
			config = config,
			content = f'An unknown error has occurred:\n```{error}\n```',
			responseType = 'error'
		)


async def setup(bot: commands.Bot):
	await bot.add_cog(Queue(bot))