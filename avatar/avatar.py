import discord
from redbot.core import commands

__author__ = "Issy"


class AvatarCog(commands.Cog):
    """See another member's avatar bigly"""

    def __init__(self, bot):
        self.bot = bot

    # Commands

    @commands.guild_only()
    @commands.command(name="avatar")
    async def _avatar(self, ctx, member: discord.Member):
        """See another member's avatar"""
        avatar_embed = self.make_embed(member)
        await ctx.send(avatar_embed)

    def make_embed(self, member: discord.Member) -> discord.Embed:
        embed = discord.Embed(title=member.name, colour=member.colour)
        embed.set_image(url=member.avatar_url)
        return embed
