from .counting import Counting
import discord

async def setup(bot):
    if discord.__version__[0] == "2":
        await bot.add_cog(Counting(bot))
    else:
        bot.add_cog(Counting(bot))