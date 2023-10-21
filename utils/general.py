import discord
import httpx

async def make_async_request(
	url: str,
	headers: dict = {},
	method: str = 'GET',
	data: dict = {},
	json: dict = {},
):
	async with httpx.AsyncClient() as client:
		if method == 'GET':
			response = await client.request(
				url = url,
				headers = headers,
				method = method,
			)
		else:
			response = await client.request(
				url = url,
				headers = headers,
				method = method,
				data = data,
				json = json
			)

	return response

async def handleResponse(
	interaction: discord.Interaction,
	config: dict,
	content: str,
	responseType: str,
	*,
	image_url: str = None,
	view: discord.ui.View = None,
	replacement_embed: discord.Embed = None
):
	if replacement_embed:
		if interaction.response.is_done():
			return await interaction.edit_original_response(embed = replacement_embed, view = view)
		else:
			return await interaction.response.send_message(embed = replacement_embed, view = view)

	embed = discord.Embed(description = content)

	# embed title and color
	match responseType:
		case 'success':
			embed.title = 'Success'
			embed.color = discord.Color.from_str(config['discord']['embed_colors']['success'])
		case 'info':
			embed.title = 'Info'
			embed.color = discord.Color.from_str(config['discord']['embed_colors']['info'])
		case 'error':
			embed.title = 'Error'
			embed.color = discord.Color.from_str(config['discord']['embed_colors']['error'])

	if image_url:
		embed.set_image(url = image_url)

	# respond with the embed
	if view:
		if interaction.response.is_done():
			return await interaction.edit_original_response(embed = embed, view = view)
		else:
			return await interaction.response.send_message(embed = embed, view = view)
	else:
		if interaction.response.is_done():
			return await interaction.edit_original_response(embed = embed)
		else:
			return await interaction.response.send_message(embed = embed)