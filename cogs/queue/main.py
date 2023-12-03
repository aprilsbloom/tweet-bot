import discord
from discord.ext import commands
from cogs.queue._views import AuthedQueueViewBasic, AuthedQueueViewExtended
from utils.general import error_response, handle_base_response, is_user_authorized
from utils.globals import POST_HR_INTERVAL, cfg
from datetime import datetime, timedelta

class Queue(commands.Cog):
	def __init__(self, bot: commands.Bot):
		self.bot = bot

	group = discord.app_commands.Group(name = 'queue', description = 'Commands to manage the post queue.')

	@group.command(name = 'view', description = 'View the post queue.')
	async def queue_view(self, interaction: discord.Interaction):
		bot_info = await self.bot.application_info()
		queue = cfg.get('queue')
		queue_length = len(queue)

		# If queue is empty, return
		if queue_length == 0:
			return await handle_base_response(
				interaction = interaction,
				responseType = 'info',
				content = 'The queue is empty.'
			)


		# If there is only one post in the queue, return an embed with only delete/edit buttons
		if queue_length == 1:
			embed = discord.Embed(title = "Queue list", color=discord.Color.from_str(cfg.get('discord.embed_colors.info')))

			post = queue[0]
			caption = post.get('caption', '')
			alt_text = post.get('alt_text', '')
			catbox_url = post.get('catbox_url', '')
			orig_url = post.get('original_url', '')
			author = post.get('author', '')
			emoji = post.get('emoji', '')
			base_timestamp = datetime.fromtimestamp(int(cfg.get('next_post_time')))

			# add caption field if present
			if caption != "":
				embed.add_field(name = "Caption", value = caption, inline = False)

			embed.add_field(name = "Alt text", value = alt_text, inline = False)
			embed.add_field(
				name = "Author",
				value = f"**<@{author}>** - {emoji}",
				inline = False,
			)
			embed.add_field(name = "Gif URL", value = catbox_url)
			embed.add_field(name="ETA", value=f"<t:{int(base_timestamp.timestamp())}:R>", inline=False)
			embed.set_image(url = orig_url)

			if interaction.response.is_done():
				return await interaction.edit_original_response(embed = embed, view=AuthedQueueViewBasic(post, bot_info))
			else:
				return await interaction.response.send_message(embed = embed, view=AuthedQueueViewBasic(post, bot_info))


		# If there are multiple posts in the queue, return an embed with multiple pages, and edit/delete buttons
		if queue_length > 1:
			embeds = []
			base_timestamp = datetime.fromtimestamp(int(cfg.get('next_post_time')))

			for count, post in enumerate(queue, start=1):
				embed = discord.Embed(title = "Queue list", color=discord.Color.from_str(cfg.get('discord.embed_colors.info')))

				caption = post.get('caption', '')
				alt_text = post.get('alt_text', '')
				catbox_url = post.get('catbox_url', '')
				orig_url = post.get('original_url', '')
				author = post.get('author', '')
				emoji = post.get('emoji', '')
				eta = int((base_timestamp + timedelta(hours = POST_HR_INTERVAL * (count - 1))).timestamp())

				if caption:
					embed.add_field(name = "Caption", value = caption, inline = False)

				embed.add_field(name = "Alt text", value = alt_text, inline = False)
				embed.add_field(
					name = "Author",
					value = f"**<@{author}>** - {emoji}",
					inline = False,
				)
				embed.add_field(name = "Gif URL", value = catbox_url, inline = False)
				embed.add_field(name="ETA", value=f"<t:{eta}:R>", inline=False)
				embed.set_image(url = orig_url)
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


	@group.command(name = 'remove', description = "Remove an item from the queue")
	async def queue_remove(self, interaction: discord.Interaction, url: str):
		queue = cfg.get('queue')
		queue_length = len(queue)
		bot_info = await self.bot.application_info()


		# If user isn't authed, return
		if not is_user_authorized(interaction.user.id, bot_info):
			return await handle_base_response(
				interaction = interaction,
				content = "You do not have permission to run this command.\nPlease ask an administrator for access if you believe this to be in error.",
				responseType = "error",
			)


		# If queue is empty, return
		if queue_length == 0:
			return await handle_base_response(
				interaction = interaction,
				content = "The tweet queue is empty. Please try again later",
				responseType = "error",
			)


		# Find the post in the queue given the URL
		foundGif = False
		for post in queue.copy():
			if post["catbox_url"] == url or post["original_url"] == url:
				queue.remove(post)
				foundGif = True

		cfg.set('queue', queue)


		if foundGif:
			# If the post was found, return success
			return await handle_base_response(
				interaction=interaction,
				content="The URL you have entered has been successfully removed from the queue",
				responseType="success",
			)

		else:
			# If the post was not found, return error
			await handle_base_response(
				interaction=interaction,
				content="The URL you have entered was not found in the queue.",
				responseType="error",
			)

	@queue_remove.error
	async def queue_remove_error(self, interaction: discord.Interaction, error):
		return await error_response(interaction, error, '/queue remove')


async def setup(bot: commands.Bot):
	await bot.add_cog(Queue(bot))