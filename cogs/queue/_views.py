import discord
from utils.general import is_user_authorized, create_embed, handleResponse
from utils.config import load_config, write_config
from utils.logger import Logger

log = Logger()

# Tweet editing modal
class EditTweetModal(discord.ui.Modal):
	def __init__(self, post, title="Edit post"):
		super().__init__(title=title)
		self.config = load_config()
		self.post = post
		self.add_inputs()

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

	async def on_submit(self, interaction: discord.Interaction):
		self.update_post_config()
		await self.send_edit_message(interaction)

	def update_post_config(self):
		config = load_config()
		for post in config["twitter"]["queue"]:
			if post["catbox_url"] == self.post["catbox_url"]:
				post_index = config["twitter"]["queue"].index(post)
				config["twitter"]["queue"][post_index]["caption"] = self.children[0].value
				config["twitter"]["queue"][post_index]["alt_text"] = self.children[1].value
				write_config(config)

	async def send_edit_message(self, interaction):
		config = load_config()
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
		_button: discord.ui.Button
	):
		config = load_config()
		if not is_user_authorized(interaction.user.id, self.bot_info):
			return await interaction.response.send_message(
				embed=self.create_embed(
					"Error",
					"You do not have permission to delete posts.\nPlease ask an administrator for access if you believe this to be in error.",
					'error'
				),
				ephemeral=True,
			)

		config["twitter"]["queue"].remove(self.post)
		write_config(config)

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
		_button: discord.ui.Button
	):
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


# Authed queue viewing (basic, comes without previous and next buttons)
class AuthedQueueViewBasic(discord.ui.View):
	def __init__(self, post, bot_info):
		super().__init__()
		self.post = post
		self.bot_info = bot_info

	@discord.ui.button(label = "Delete", style = discord.ButtonStyle.red)
	async def delete(
		self,
		interaction: discord.Interaction,
		_button: discord.ui.Button
	):
		if not is_user_authorized(interaction.user.id, self.bot_info):
			return await interaction.response.send_message(
				embed = create_embed(
					"Error",
					"You do not have permission to delete posts.\nPlease ask an administrator for access if you believe this to be in error.",
					'error'
				),
				ephemeral = True
			)

		return await interaction.response.send_message(
			embed = create_embed(
				"Confirmation",
				"Are you sure you want to delete this post?",
				'info'
			),
			view = DeleteConfirmation(post = self.post, bot_info = self.bot_info),
			ephemeral = True
		)

	@discord.ui.button(label = "Edit", style = discord.ButtonStyle.grey)
	async def edit(
		self,
		interaction: discord.Interaction,
		_button: discord.ui.Button
	):
		if not is_user_authorized(interaction.user.id, self.bot_info):
			return await interaction.response.send_message(
				embed = create_embed(
					"Error",
					"You do not have permission to edit posts.\nPlease ask an administrator for access if you believe this to be in error.",
					'error'
				),
				ephemeral = True
			)

		await interaction.response.send_modal(EditTweetModal(post = self.post))

# Authed queue viewing (extended, comes with previous and next buttons)
class AuthedQueueViewExtended(discord.ui.View):
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
		_button: discord.ui.Button
	):
		config = load_config()
		if not is_user_authorized(interaction.user.id, self.bot_info):
			return await interaction.response.send_message(
				embed = create_embed(
					"Error",
					"You do not have permission to delete posts.\nPlease ask an administrator for access if you believe this to be in error.",
					'error'
				),
				ephemeral = True
			)

		await interaction.response.send_message(
			embed = create_embed(
				"Confirmation",
				"Are you sure you want to delete this post?",
				'info'
			),
			view = DeleteConfirmation(post = self.post, bot_info = self.bot_info)
		)

	@discord.ui.button(label = "Edit", style = discord.ButtonStyle.grey)
	async def edit(self, interaction: discord.Interaction, _button: discord.ui.Button):
		config = load_config()
		if not is_user_authorized(interaction.user.id, self.bot_info):
			return await interaction.response.send_message(
				embed = create_embed(
					"Error",
					"You do not have permission to edit posts.\nPlease ask an administrator for access if you believe this to be in error.",
					'error'
				),
				ephemeral = True
			)

		await interaction.response.send_modal(EditTweetModal(post = self.post))

	@discord.ui.button(label = "Previous", style = discord.ButtonStyle.grey, disabled = True)
	async def previous(
		self,
		interaction: discord.Interaction,
		_button: discord.ui.Button
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
		_button: discord.ui.Button
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