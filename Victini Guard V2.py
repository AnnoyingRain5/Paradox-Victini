import discord
import os
from dotenv import load_dotenv
from discord.ext.commands import CheckFailure
import sys
import traceback
from io import StringIO

load_dotenv()  # load env vars from file

# set up intents
intents = discord.Intents.default()
intents += discord.Intents.message_content

bot = discord.Bot(intents=intents)

@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')
    await bot.change_presence(activity=discord.Game(name="with other Victinis!"))

@bot.event
async def on_message(ctx):
    if ctx.author == bot.user:
        return

    if ctx.channel.id == 981343621104140308:
        await ctx.add_reaction(":vyes:1054227682944110612")
        await ctx.add_reaction(":vno:1054227685016092833")
        
    if ctx.channel.id == 809238709635383327:
        if ctx.attachments == [] and "http" not in ctx.content:
            await ctx.delete()
            await ctx.author.send("You can only send your art in <#809238709635383327>, all messages must contain art or a link to it!")
    
    if isinstance(ctx.channel, discord.DMChannel):
        info = await bot.application_info()
        await info.owner.send("You have a new DM from " + ctx.author.name + " (" + ctx.author.mention + "):\n" + ctx.content)
    
@bot.slash_command(description="Ping the bot!")
async def ping(ctx):
    await ctx.respond(f"Pong! {round(bot.latency * 1000)}ms")

@bot.slash_command(description="owner only command")
async def senddm(ctx, user: discord.User, message: str):
    info = await bot.application_info()
    if ctx.author == info.owner:
        await user.send(message)
        await ctx.respond(f"Sent \"{message}\" to {user.mention}!", ephemeral=True)
    else:
        await ctx.respond("No.")
    

# Global command error handler
@bot.event
async def on_application_command_error(ctx, error):
    # Check failures should be handled by the individual cogs, not here.
    if not isinstance(error, CheckFailure):
        await ctx.send(f"An error occured and has been automatically reported to the developer. Error: `{error}`")
        info = await bot.application_info()
        sio = StringIO()
        # traceback requires a file-like object, so we use StringIO to get the traceback as a string
        traceback.print_exception(error, file=sio, limit=4)
        tb = sio.getvalue()  # get the string from the StringIO object
        if ctx.guild != None:
            message = f"An error occurred in {ctx.guild.name} ({ctx.guild.id}) in {ctx.channel.name} ({ctx.channel.mention}) by {ctx.author.name} ({ctx.author.mention})\n"
        else:
             message = f"An error occurred in A DM with {ctx.author.name} ({ctx.author.mention})\n"
        message += f"Error: `{error}`\n The traceback will be supplied in the next message."
        await info.owner.send(message)
        await info.owner.send(f"```py\n{tb}```")


# Global non-command error handler
@bot.event
async def on_error(event, *args, **kwargs):
    info = await bot.application_info()
    sio = StringIO()
    # traceback requires a file-like object, so we use StringIO to get the traceback as a string
    traceback.print_exc(file=sio, limit=4)
    tb = sio.getvalue()  # get the string from the StringIO object
    message = f"The following error occurred in `{event}`:\nargs: ```py\n{args}```\nkwargs:```py\n{kwargs}```\n\n"
    message += f"Error type: `{sys.exc_info()[0]}`\nError value: `{sys.exc_info()[1]}`\nThe traceback will be supplied in the next message."
    await info.owner.send(message)
    await info.owner.send(f"```py\n{tb}```")
    
bot.run(os.getenv('TOKEN'))