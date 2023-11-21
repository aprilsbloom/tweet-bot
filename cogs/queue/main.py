import discord
from discord.ext import commands
from cogs.queue._views import AuthedQueueViewBasic, AuthedQueueViewExtended
from utils.general import error_response, handle_base_response, is_user_authorized
from utils.config import load_config, write_config



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

		# If queue is empty, return
		if queue_length == 0:
			return await handle_base_response(
				interaction = interaction,
				config = config,
				responseType = 'info',
				content = 'The queue is empty.'
			)

		# If there is only one post in the queue, return an embed with only delete/edit buttons
		if queue_length == 1:
			embed = discord.Embed(title = "Queue list", color=discord.Color.from_str(config["discord"]["embed_colors"]["info"]))
			post = config["twitter"]["queue"][0]
			author_user = post["author"]
			author_emoji = post["emoji"]

			# add caption field if present
			if post["caption"] != "":
				embed.add_field(name = "Caption", value = post["caption"], inline = False)

			embed.add_field(name = "Alt text", value = post["alt_text"], inline = False)
			embed.add_field(
				name = "Author",
				value = f"**<@{author_user}>** - {author_emoji}",
				inline = False,
			)
			embed.add_field(name = "Gif URL", value = post["catbox_url"])
			embed.set_image(url = post["catbox_url"])

			if interaction.response.is_done():
				return await interaction.edit_original_response(embed = embed, view=AuthedQueueViewBasic(post, bot_info))
			else:
				return await interaction.response.send_message(embed = embed, view=AuthedQueueViewBasic(post, bot_info))

		# If there are multiple posts in the queue, return an embed with multiple pages, and edit/delete buttons
		if queue_length > 1:
			embeds = []

			for count, post in enumerate(config["twitter"]["queue"], start=1):
				embed = discord.Embed(title = "Queue list", color=discord.Color.from_str(config["discord"]["embed_colors"]["info"]))
				author_user = post["author"]
				author_emoji = post["emoji"]

				if post.get("caption", ""):
					embed.add_field(name = "Caption", value = post["caption"], inline = False)

				embed.add_field(name = "Alt text", value = post["alt_text"], inline = False)
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
		return await error_response(interaction, error, '/queue view')

	@group.command(
		name = 'remove',
		description = "Remove an item from the queue"
	)
	async def queue_remove(self, interaction: discord.Interaction, url: str):
		config = load_config()
		queue_length = len(config["twitter"]["queue"])
		bot_info = await self.bot.application_info()

		# If user isn't authed, return
		if not is_user_authorized(interaction.user.id, bot_info):
			return await handle_base_response(
				interaction = interaction,
				config = config,
				content = "You do not have permission to run this command.\nPlease ask an administrator for access if you believe this to be in error.",
				responseType = "error",
			)

		# If queue is empty, return
		if queue_length == 0:
			return await handle_base_response(
				interaction = interaction,
				config = config,
				content = "The tweet queue is empty. Please try again later",
				responseType = "error",
			)

		# Find the post in the queue given the URL
		foundGif = False
		for post in config.copy()["twitter"]["queue"]:
			if post["catbox_url"] == url:
				config["twitter"]["queue"].remove(post)
				write_config(config)
				foundGif = True

		# If the post was found, return success
		if foundGif:
			return await handle_base_response(
				interaction=interaction,
				config=config,
				content="The URL you have entered has been successfully removed from the queue",
				responseType="success",
			)
		# If the post was not found, return error
		else:
			await handle_base_response(
				interaction=interaction,
				config=config,
				content="The URL you have entered was not found in the queue.",
				responseType="error",
			)

	@queue_remove.error
	async def queue_remove_error(self, interaction: discord.Interaction, error):
		return await error_response(interaction, error, '/queue remove')


async def setup(bot: commands.Bot):
	await bot.add_cog(Queue(bot))