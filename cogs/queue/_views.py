import discord
from cogs.queue._utils import remove_post, edit_post, delete_response, edit_response
from utils.general import is_user_authorized, create_embed, handleResponse
from utils.config import load_config, write_config
from utils.logger import Logger

class EditPostModal(discord.ui.Modal):
	"""
	Modal to edit a post within the queue

	Args
	----
		- post (dict): The post to edit
		- title (Optional[str]): The title of the modal
	"""

	def __init__(self, post, title="Edit post"):
		super().__init__(title=title)
		self.config = load_config()
		self.post = post
		self.add_inputs()

	# Add our text inputs to the modal
	def add_inputs(self):
		self.add_item(
			discord.ui.TextInput(
				label="Caption",
				default=self.post["caption"],
				max_length=280,
				style=discord.TextStyle.long,
			)
		)
		self.add_item(
			discord.ui.TextInput(
				label="Alt text",
				default=self.post["alt_text"],
				min_length=1,
				max_length=1000,
				style=discord.TextStyle.long,
			)
		)

	# Whenever the user submits the modal, update the post config and send a message
	async def on_submit(self, interaction: discord.Interaction):
		await edit_post(self.post, {
			'caption': self.children[0].value,
			'alt_text': self.children[1].value
		})
		await self.send_edit_message(interaction)

	# Send a message to the user letting them know the post has been edited
	async def send_edit_message(self, interaction):
		return await interaction.response.send_message(
			embed=create_embed(
				"Success",
				"Post has been edited.",
				'success'
			),
			ephemeral=True
		)

class DeleteConfirmation(discord.ui.View):
	def __init__(self, post, bot_info):
		super().__init__()
		self.post = post
		self.bot_info = bot_info
		self.create_embed = self.create_embed

	@discord.ui.button(label = "Yes", style = discord.ButtonStyle.red)
	async def deletion_confirmed(
		self,
		interaction: discord.Interaction,
		_
	):
		# If the user is not authorized, return an error
		if not is_user_authorized(interaction.user.id, self.bot_info):
			return await interaction.response.send_message(
				embed=self.create_embed(
					"Error",
					"You do not have permission to delete posts.\nPlease ask an administrator for access if you believe this to be in error.",
					'error'
				),
				ephemeral=True,
			)

		await remove_post(self.post)

		return await interaction.response.send_message(
			embed=self.create_embed(
				"Success",
				"Post has been deleted.",
				'success'
			),
			ephemeral=True
		)

	@discord.ui.button(label = "No", style = discord.ButtonStyle.grey)
	async def deletion_dismissed(
		self,
		interaction: discord.Interaction,
		_
	):
		# If the user is not authorized, return an error
		if not is_user_authorized(interaction.user.id, self.bot_info):
			return await interaction.response.send_message(
				embed = self.create_embed(
					'Error',
					'You do not have permission to interact with this command.\nPlease ask an administrator for access if you believe this to be in error.',
					'error'
				),
				ephemeral = True
			)

		await interaction.response.send_message(
			embed = self.create_embed(
				'Info',
				'Post was not deleted.',
				'info'
			),
			ephemeral = True
		)

class AuthedQueueViewBasic(discord.ui.View):
	"""
	Authed queue viewing (basic, comes without previous and next buttons)

	Args
	----
		- post (dict): The post to view
		- bot_info (discord.AppInfo): The bot's application info
	"""
	def __init__(self, post, bot_info):
		super().__init__()
		self.post = post
		self.bot_info = bot_info

	@discord.ui.button(label = "Delete", style = discord.ButtonStyle.red)
	async def delete(
		self,
		interaction: discord.Interaction,
		_
	):
		return await delete_response(interaction, self.bot_info, self.post)

	@discord.ui.button(label = "Edit", style = discord.ButtonStyle.grey)
	async def edit(
		self,
		interaction: discord.Interaction,
		_
	):
		return await edit_response(interaction, self.bot_info, self.post)

class AuthedQueueViewExtended(discord.ui.View):
	"""
	Authed queue viewing (extended, comes with previous and next buttons)

	Args
	----
		- pages (list): The pages to view
			- These are formatted as a list of objects, which contain both the post object and the embed associated with it
		- bot_info (discord.AppInfo): The bot's application info
	"""

	def __init__(
		self,
		pages: list,
		bot_info
	):
		super().__init__()
		self.pages = pages
		self.bot_info = bot_info

		self.current_page = 0
		self.post = pages[0]["post"]

	@discord.ui.button(label = "Delete", style = discord.ButtonStyle.red)
	async def delete(
		self,
		interaction:
		discord.Interaction,
		_
	):
		return await delete_response(interaction, self.bot_info, self.post)

	@discord.ui.button(label = "Edit", style = discord.ButtonStyle.grey)
	async def edit(self, interaction: discord.Interaction, _):
		return await edit_response(interaction, self.bot_info, self.post)

	@discord.ui.button(label = "Previous", style = discord.ButtonStyle.grey, disabled = True)
	async def previous(
		self,
		interaction: discord.Interaction,
		_
	):
		self.current_page -=  1

		for child in self.children:
			child.disabled = child.label == "Previous" if self.current_page == 0 else False

		self.post = self.pages[self.current_page]["post"]
		embed = self.pages[self.current_page]["embed"]
		await interaction.response.edit_message(
			embed = embed,
			view = self
		)

	@discord.ui.button(label = "Next", style = discord.ButtonStyle.grey)
	async def next(
		self,
		interaction: discord.Interaction,
		_
	):
		self.current_page += 1

		for child in self.children:
			if self.current_page == len(self.pages) - 1:
				child.disabled = child.label == "Next"
			else:
				child.disabled = False

		self.post = self.pages[self.current_page]["post"]
		embed = self.pages[self.current_page]["embed"]
		await interaction.response.edit_message(
			embed = embed,
			view = self
		)