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
	responseType: str
):
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

	# respond with the embed
	if interaction.response.is_done():
		return await interaction.edit_original_response(embed = embed)
	else:
		return await interaction.response.send_message(embed = embed)