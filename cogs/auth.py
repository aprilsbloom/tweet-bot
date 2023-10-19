import discord
from discord.ext import commands

# Command
class Help(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @discord.app_commands.command(name = 'test', description = 'a')
    async def help(self, interaction: discord.Interaction):
        embed=discord.Embed(title='test', description='hi')

        await interaction.response.send_message(embed=embed)

# Cog setup
async def setup(bot: commands.Bot):
    await bot.add_cog(Help(bot))