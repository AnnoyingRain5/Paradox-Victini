import discord
import os
from dotenv import load_dotenv
from discord.ext.commands import CheckFailure
import sys
import traceback
from io import StringIO
from discord.commands.context import ApplicationContext as SlashContext

load_dotenv()  # load env vars from file

# set up intents
intents = discord.Intents.default()
intents += discord.Intents.message_content
bot = discord.Bot(intents=intents)

QNA_CHANNEL_ID = 1094266918556422204


@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')
    await bot.change_presence(activity=discord.Game(name="with other Victinis!"))


@bot.event
async def on_message(ctx: discord.Message):
    if ctx.author == bot.user:
        return

    # if the channel is polls
    if ctx.channel.id == QNA_CHANNEL_ID:
        if ctx.content.endswith("?"):
            response = f"Hey {ctx.author.mention}!\n"
            response += "If this is a question of the day, please mark it as such by using /ask!\n"
            response += "This message will self destruct in 10 seconds"
            await ctx.channel.send(response, delete_after=10)

    # if the channel is artwork showcase
    if ctx.channel.id == 809238709635383327:
        if ctx.attachments == [] and "http" not in ctx.content:
            await ctx.delete()
            await ctx.author.send("You can only send your art in <#809238709635383327>, all messages must contain art or a link to it!")

    # if the channnel is a DM
    if isinstance(ctx.channel, discord.DMChannel):
        info = await bot.application_info()
        await info.owner.send("You have a new DM from " + ctx.author.name + " (" + ctx.author.mention + "):\n" + ctx.content)


# main commands

@bot.slash_command(description="Ping the bot!")
async def ping(ctx: SlashContext):
    await ctx.respond(f"Pong! {round(bot.latency * 1000)}ms")


@bot.slash_command(description="Get the source code!")
async def github(ctx: SlashContext):
    await ctx.respond("check out my source code here: https://github.com/AnnoyingRain5/Victini-Guard, and send a PR if you're feeling kind!")


@bot.slash_command(description="Format a question for the QnA channel!")
async def ask(ctx: SlashContext, question: str):
    if not isinstance(ctx.channel, discord.TextChannel):
        await ctx.respond("This command can only be run in text channels")
        return
    if ctx.channel.id != QNA_CHANNEL_ID:
        await ctx.respond(f"This needs to be used in the {bot.get_channel(QNA_CHANNEL_ID).mention} channel!", ephemeral=True)
        return
    embed = discord.Embed()
    embed.set_author(name=ctx.author.name, icon_url=ctx.author.display_avatar)
    embed.title = question
    embed.set_footer(text=f"New question by {ctx.author.name}")
    embed.color = 0x20a303
    await ctx.respond(embed=embed)


@bot.slash_command(description="Set up a poll!")
async def poll(ctx: SlashContext, poll: str):
    # ensure we are in a text channel
    if not isinstance(ctx.channel, discord.TextChannel):
        await ctx.respond("This command can only be run in text channels")
        return
    # ensure we are in the polls channel
    if ctx.channel.id != QNA_CHANNEL_ID:
        await ctx.respond(f"This needs to be used in the {bot.get_channel(QNA_CHANNEL_ID).mention} channel!", ephemeral=True)
        return
    embed = discord.Embed()
    embed.set_author(name=ctx.author.name, icon_url=ctx.author.display_avatar)
    embed.title = poll
    embed.set_footer(text=f"New poll by {ctx.author.name}")
    embed.color = 0x2b34cf
    await ctx.respond(embed=embed)
    # Find the message that we just posted in the history
    async for message in ctx.channel.history():
        if not message.embeds:
            continue
        if message.embeds[0].author.name == embed.author.name and message.embeds[0].title == embed.title:
            # React to that message
            await message.add_reaction(":vyes:1054227682944110612")
            await message.add_reaction(":vno:1054227685016092833")
            break  # ensure we don't react more than once


# admin commands


@bot.slash_command(description="owner only command")
async def senddm(ctx: SlashContext, user: discord.User, message: str):
    info = await bot.application_info()
    if ctx.author == info.owner:
        await user.send(message)
        await ctx.respond(f"Sent \"{message}\" to {user.mention}!", ephemeral=True)
    else:
        await ctx.respond("No.")


@bot.slash_command(description="owner only command")
async def changestatus(ctx: SlashContext, status: str):
    info = await bot.application_info()
    if ctx.author == info.owner:
        await bot.change_presence(activity=discord.Game(name=status))
        await ctx.respond(f"Changed status to \"{status}\"!", ephemeral=True)
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

        if ctx.guild != None:  # if the command was run in a guild, NOT a DM
            message = f"An error occurred in {ctx.guild.name} ({ctx.guild.id}) in {ctx.channel.name} ({ctx.channel.mention}) by {ctx.author.name} ({ctx.author.mention})\n"
        else:  # command run in DM, do not include guild info
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
