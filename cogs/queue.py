import discord
from discord.ext import commands
from utils.config import fetch_data, write_data
from utils.general import handleResponse
from typing import Optional

class QueueView(discord.ui.View):
	def __init__(self, interaction: discord.Interaction, pages: list):
		super().__init__(timeout=None)
		self.pages = pages
		self.interaction = interaction
		self.current_page = 0

	@discord.ui.button(label='Previous', style=discord.ButtonStyle.grey, disabled=True)
	async def previous(self, interaction: discord.Interaction, _button: discord.ui.Button):
		self.current_page -= 1

		if self.current_page == 0:
			for i in self.children:
				if i.label == 'Previous':
					i.disabled = True
				elif i.label == 'Next':
					i.disabled = False
		else:
			for i in self.children:
				if i.label == 'Previous':
					i.disabled = False
				elif i.label == 'Next':
					i.disabled = False

		await interaction.response.edit_message(embed=self.pages[self.current_page], view=self)

	@discord.ui.button(label='Next', style=discord.ButtonStyle.grey)
	async def next(self, interaction: discord.Interaction, _button: discord.ui.Button):
		self.current_page += 1

		if self.current_page == len(self.pages) - 1:
			for i in self.children:
				if i.label == 'Next':
					i.disabled = True
				elif i.label == 'Previous':
					i.disabled = False
		else:
			for i in self.children:
				if i.label == 'Next':
					i.disabled = False
				elif i.label == 'Previous':
					i.disabled = False

		await interaction.response.edit_message(embed=self.pages[self.current_page], view=self)

# Command
class Queue(commands.Cog):
	def __init__(self, bot: commands.Bot):
		self.bot = bot

	@discord.app_commands.command(name = 'queue', description = 'View / remove items from the tweet queue')
	@discord.app_commands.describe(url = 'The GIF url you wish to remove from the queue (optional)')
	@discord.app_commands.choices(cmd_choice = [
		discord.app_commands.Choice(name = 'View', value = 'view'),
		discord.app_commands.Choice(name = 'Remove', value = 'remove'),
	])
	async def queue(self, interaction: discord.Interaction, cmd_choice: discord.app_commands.Choice[str], url: Optional[str] = ''):
		config = fetch_data()
		bot_info = await self.bot.application_info()

		# structure
		# config['twitter']['post_queue'].append(
		# 	{
		# 		'original_url': clean_url,
		# 		'catbox_url': res_catbox.text,
		# 		'author': interaction.user.id,
		# 		'emoji': emoji,
		# 		'caption': caption,
		# 		'alt_text': alt_text
		# 	}
		# )

		post_queue_length = len(config['twitter']['post_queue'])
		if post_queue_length == 0:
				return await handleResponse(
					interaction = interaction,
					config = config,
					content = 'The tweet queue is empty. Please try again later',
					responseType = 'error'
				)

		if cmd_choice.value == 'view':
			if post_queue_length > 1:
				embeds = []
				count = 0

				for post in config['twitter']['post_queue']:
					count += 1
					embed = discord.Embed(title = 'Queue list')

					if post['caption'] != '':
						embed.add_field(name = 'Caption', value = post['caption'], inline = False)

					embed.add_field(name = 'Alt text', value = post['alt_text'], inline = False)

					author_user = post['author']
					author_emoji = post['emoji']

					embed.add_field(name = 'Author', value = f'**<@{author_user}>** - {author_emoji}', inline = False)
					embed.add_field(name = 'Gif URL', value = post['catbox_url'])
					embed.set_image(url = post['catbox_url'])
					embed.set_footer(text = f'Post {count} / {post_queue_length}')

					embeds.append(embed)

				return await handleResponse(
					interaction = interaction,
					config = config,
					content = '',
					responseType = '',
					view = QueueView(interaction, embeds),
					replacement_embed = embeds[0]
				)
			else:
					post = config['twitter']['post_queue'][0]
					embed = discord.Embed(title = 'Queue list')

					if post['caption'] != '':
						embed.add_field(name = 'Caption', value = post['caption'], inline = False)

					embed.add_field(name = 'Alt text', value = post['alt_text'], inline = False)

					author_user = post['author']
					author_emoji = post['emoji']

					embed.add_field(name = 'Author', value = f'**<@{author_user}>** - {author_emoji}', inline = False)
					embed.add_field(name = 'Gif URL', value = post['catbox_url'])
					embed.set_image(url = post['catbox_url'])
					embed.set_footer(text = f'Post {post_queue_length} / {post_queue_length}')

					return await handleResponse(
						interaction = interaction,
						config = config,
						content = '',
						responseType = '',
						replacement_embed = embed
					)
		elif cmd_choice.value == 'remove':
			if interaction.user.id not in config['discord']['authed_users'] and interaction.user.id != bot_info.owner.id:
				return await handleResponse(
					interaction = interaction,
					config = config,
					content = 'You do not have permission to run this command.\nPlease ask an administrator for access if you believe this to be in error.',
					responseType = 'error'
				)

			if url == '':
				return await handleResponse(
					interaction = interaction,
					config = config,
					content = 'You have not entered a URL to remove from the queue.',
					responseType = 'error'
				)
			else:
				foundGif = False

				for post in config.copy()['twitter']['post_queue']:
					if post['catbox_url'] == url:
						config['twitter']['post_queue'].remove(post)
						write_data(config)
						foundGif = True

				if foundGif == False:
					return await handleResponse(
						interaction = interaction,
						config = config,
						content = 'The URL you have entered was not found in the queue.',
						responseType = 'error'
					)
				else:
					return await handleResponse(
						interaction = interaction,
						config = config,
						content = 'The URL you have entered has been successfully removed from the queue',
						responseType = 'success'
					)


	@queue.error
	async def queue_error(self, interaction: discord.Interaction, error):
		config = fetch_data()
		return await handleResponse(
			interaction = interaction,
			config = config,
			content = f'An unknown error has occurred:\n```\n{error}\n```',
			responseType = 'error'
		)


# Cog setup
async def setup(bot: commands.Bot):
	await bot.add_cog(Queue(bot))