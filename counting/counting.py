import asyncio
import datetime
import discord
import typing

from discord.utils import get, find
from redbot.core import Config, checks, commands
from redbot.core.bot import Red

class Counting(commands.Cog):
    """
    Make a counting channel with goals.
    """

    __version__ = "1.4.0a"

    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(
            self, identifier=1564646215646, force_registration=True
        )

        self.config.register_guild(
            channel=0,
            previous=0,
            goal=0,
            last=0,
            whitelist=None,
            warning=False,
            seconds=0,
            topic=True,
        )

    async def red_delete_data_for_user(self, *, requester, user_id):
        for guild in self.bot.guilds:
            if user_id == await self.config.guild(guild).last():
                await self.config.guild(guild).last.clear()

    def format_help_for_context(self, ctx: commands.Context) -> str:
        context = super().format_help_for_context(ctx)
        return f"{context}\n\nVersion: {self.__version__}"

    @commands.command()
    async def countinfo(self, ctx):
        """Info on Counting (beta)"""
        embed = discord.Embed(title="Info on Counting", color=await ctx.embed_color())
        embed.add_field(name="notes", value=f"• feel free to report bugs with {ctx.prefix}contact\n•messages containing the wrong count or a character other than , or : directly after a count will be deleted\n•double counts will also be deleted\n•counts that have been deleted or edited to be wrong will not affect the count")
        await ctx.send(embed=embed)

    @checks.admin()
    @checks.bot_has_permissions(manage_channels=True, manage_messages=True)
    @commands.group(autohelp=True, aliases=["counting"])
    @commands.guild_only()
    async def countset(self, ctx: commands.Context):
        """Various Counting settings."""

    @countset.command(name="channel")
    async def countset_channel(self, ctx: commands.Context, channel: typing.Optional[discord.TextChannel]):
        """Set the counting channel.

        If a channel isn't provided, it will remove the current channel."""
        if not channel:
            await self.config.guild(ctx.guild).channel.set(0)
            return await ctx.send("Channel removed.")
        await self.config.guild(ctx.guild).channel.set(channel.id)
        await ctx.send(f"{channel.mention} has been set for counting.")

    @countset.command(name="start")
    async def countset_start(self, ctx: commands.Context, number: int):
        """Set the starting number."""
        channel = ctx.guild.get_channel(await self.config.guild(ctx.guild).channel())
        if not channel:
            return await ctx.send(f"Set the channel with `{ctx.prefix}countset channel <channel>`, please.")
        await self.config.guild(ctx.guild).previous.set(number)
        await self.config.guild(ctx.guild).last.clear()
        next_number = number + 1
        try:
            await channel.send(number)
        except (discord.Forbidden, discord.NotFound):
            return await ctx.send(f"Unable to send starting number. Make sure {ctx.bot.user.display_name} has proper permissions and that the channel exists.")
        if channel.id != ctx.channel.id:
            await ctx.send(f"Counting start set to {number}.")

    @countset.command(name="settings")
    async def countset_settings(self, ctx: commands.Context):
        """See current settings."""
        data = await self.config.guild(ctx.guild).all()
        channel = ctx.guild.get_channel(data["channel"])
        channel = channel.mention if channel else "None"
        embed = discord.Embed(color=await ctx.embed_color(), timestamp=datetime.datetime.utcnow())
        if ctx.guild.icon:
            if discord.__version__[0] == "2":
                url = str(ctx.guild.icon.replace(size=1024, format="webp")) + "?quality=lossless"
            else:
                url=str(ctx.guild.icon_url) + "&quality=lossless"
                if ctx.guild.is_icon_animated():
                    url=ctx.guild.icon_url_as(format="gif", size=2048)
        try:
            url
        except:
            url = None
        embed.set_author(name=ctx.guild.name, icon_url=url)
        embed.title = "**__Counting settings:__**"
        embed.set_footer(text="*required to function properly")
        embed.add_field(name="Channel*:", value=channel)
        embed.add_field(name="Next number:", value=str(data["previous"] + 1))
        await ctx.send(embed=embed)
    
    @commands.Cog.listener()
    async def on_message(self, message):
        if not message.guild or message.author.id == self.bot.user.id:
            return
        if message.channel.id != await self.config.guild(message.guild).channel():
            return
        last_id = await self.config.guild(message.guild).last()
        previous = await self.config.guild(message.guild).previous()
        next_number = previous + 1
        goal = await self.config.guild(message.guild).goal()
        seconds = await self.config.guild(message.guild).seconds()
        if message.author.id != last_id:
            try:
                x = (message.content.strip().split()[0])
                transTable = x.maketrans("6", "6", ",:")
                y = x.translate(transTable)
                now = int(y)
                if now - 1 == previous:
                    await self.config.guild(message.guild).previous.set(now)
                    await self.config.guild(message.guild).last.set(message.author.id)
                    n = now + 1
                    return
            except ValueError:
                pass
        try:
            await message.delete()
        except (discord.Forbidden, discord.NotFound):
            pass

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if not message.guild:
            return
        if message.channel.id != await self.config.guild(message.guild).channel():
            return
        try:
            x = (message.content.strip().split()[0])
            transTable = x.maketrans("6", "6", ",:")
            y = x.translate(transTable)
            deleted = int(y)
            previous = await self.config.guild(message.guild).previous()
            if deleted == previous:
                s = str(deleted)
                msgs = await message.channel.history(limit=1).flatten()
                msg = find(lambda m: m.content == s, msgs)
                if not msg:
                    p = deleted
                    await self.config.guild(message.guild).previous.set(p)
                    await message.channel.send(deleted)
        except (TypeError, ValueError):
            return