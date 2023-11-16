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
intents += discord.Intents.members
bot = discord.Bot(intents=intents)

QNA_CHANNEL_ID = 1094266918556422204
COUNT_CHANNEL_ID = 838432869248008203

REACTION_ROLES_DICT = {
    937181442620915773: 840409170443894804,  # art project participation
    937181709349298217: 936114664289488939,  # voice chat stream ping
    982104145907576863: 982099311921881089,  # announcement ping
}


@bot.event
async def on_ready():
    print(f"We have logged in as {bot.user}")
    await bot.change_presence(activity=discord.Game(name="with other Victinis!"))
    channel = await bot.fetch_channel(757682443120541888)
    for messageid in REACTION_ROLES_DICT.keys():
        message = await channel.fetch_message(messageid)
        for reaction in message.reactions:
            for user in await reaction.users().flatten():
                role: discord.Role = channel.guild.get_role(REACTION_ROLES_DICT[messageid])  # type: ignore
                if type(user) == discord.member:
                    await user.add_roles(role)
                else:
                    print("Removing reaction from: " + str(user.name))
                    await reaction.remove(user)


@bot.event
async def on_message(ctx: discord.Message):
    if ctx.author == bot.user:
        return

    # if the channel is artwork showcase
    if ctx.channel.id == 809238709635383327:
        if ctx.attachments == [] and "http" not in ctx.content:
            await ctx.delete()
            await ctx.author.send(
                "You can only send your art in <#809238709635383327>, all messages must contain art or a link to it!"
            )
    if ctx.channel.id == COUNT_CHANNEL_ID:
        message = await ctx.channel.history(limit=2).flatten()
        message = message[1]
        if message is None:
            # this should not happen
            raise Exception("could not fetch last message")
        if ctx.author.id == message.author.id:
            await ctx.delete()

    # if the channnel is a DM
    if isinstance(ctx.channel, discord.DMChannel):
        info = await bot.application_info()
        await info.owner.send(
            "You have a new DM from "
            + ctx.author.name
            + " ("
            + ctx.author.mention
            + "):\n"
            + ctx.content
        )


@bot.event
async def on_raw_reaction_add(payload: discord.RawReactionActionEvent):
    if payload.message_id in REACTION_ROLES_DICT.keys():
        guild = await bot.fetch_guild(payload.guild_id)
        role: discord.Role = guild.get_role(REACTION_ROLES_DICT[payload.message_id])  # type: ignore
        await payload.member.add_roles(role)


@bot.event
async def on_raw_reaction_remove(payload: discord.RawReactionActionEvent):
    if payload.message_id in REACTION_ROLES_DICT.keys():
        guild = await bot.fetch_guild(payload.guild_id)
        role: discord.Role = guild.get_role(REACTION_ROLES_DICT[payload.message_id])  # type: ignore
        try:
            member = await guild.fetch_member(payload.user_id)
        except:  # user has left
            return
        await member.remove_roles(role)


@bot.event
async def on_member_update(before: discord.Member, after: discord.Member):
    if before.roles != after.roles:
        for role in before.roles:
            if role.color.value != 0:
                if len(role.members) == 0:
                    print("deleting role ", role.name)
                    await role.delete()


@bot.event
async def on_raw_member_remove(payload: discord.RawMemberRemoveEvent):
    for role in await bot.get_guild(payload.guild_id).fetch_roles():
        if role.color.value != 0:
            if len(role.members) == 0:
                print("deleting role ", role.name)
                await role.delete()


# main commands


@bot.slash_command(description="Ping the bot!")
async def ping(ctx: SlashContext):
    await ctx.respond(f"Pong! {round(bot.latency * 1000)}ms", ephemeral=True)


@bot.slash_command(description="Remove all unused color roles, owner only")
async def remove_unused_colors(ctx: SlashContext):
    info = await bot.application_info()
    if ctx.author == info.owner:
        for role in await ctx.guild.fetch_roles():
            if role.color.value != 0:
                if len(role.members) == 0:
                    print("deleting role ", role.name)
                    await role.delete()
        await ctx.respond("done!", ephemeral=True)
    else:
        await ctx.respond("no", ephemeral=True)


@bot.slash_command(description="Get the source code!")
async def github(ctx: SlashContext):
    await ctx.respond(
        "check out my source code here: https://github.com/AnnoyingRain5/Victini-Guard, and send a PR if you're feeling kind!"
    )


@bot.slash_command(description="Format a question for the QnA channel!")
async def ask(ctx: SlashContext, question: str):
    if not isinstance(ctx.channel, discord.TextChannel):
        await ctx.respond(
            "This command can only be run in text channels", ephemeral=True
        )
        return
    if ctx.channel.id != QNA_CHANNEL_ID:
        await ctx.respond(
            f"This needs to be used in the {bot.get_channel(QNA_CHANNEL_ID).mention} channel!",
            ephemeral=True,
        )
        return
    embed = discord.Embed()
    embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.display_avatar)
    embed.title = question
    embed.set_footer(text=f"New question by {ctx.author.display_name}")
    embed.color = 0x20A303
    await ctx.respond(embed=embed)


@bot.slash_command(description="Set up a poll!")
async def poll(ctx: SlashContext, poll: str):
    # ensure we are in a text channel
    if not isinstance(ctx.channel, discord.TextChannel):
        await ctx.respond("This command can only be run in text channels")
        return
    # ensure we are in the polls channel
    if ctx.channel.id != QNA_CHANNEL_ID:
        await ctx.respond(
            f"This needs to be used in the {bot.get_channel(QNA_CHANNEL_ID).mention} channel!",
            ephemeral=True,
        )
        return
    embed = discord.Embed()
    embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.display_avatar)
    embed.title = poll
    embed.set_footer(text=f"New poll by {ctx.author.display_name}")
    embed.color = 0x2B34CF
    await ctx.respond(embed=embed)
    # Find the message that we just posted in the history
    async for message in ctx.channel.history():
        if not message.embeds:
            continue
        if (
            message.embeds[0].author.name == embed.author.name
            and message.embeds[0].title == embed.title
        ):
            # React to that message
            await message.add_reaction(":vyes:1054227682944110612")
            await message.add_reaction(":vno:1054227685016092833")
            break  # ensure we don't react more than once


@bot.slash_command(description="Set your color!")
async def setcolor(ctx: SlashContext, color: str):
    color = color.lstrip("#")
    try:
        intcolor = int(color, 16)
        if len(color) != 6:
            raise Exception
        color = hex(intcolor)
    except Exception as e:
        colors = {
            "red": 0xFF0000,
            "green": 0x00FF00,
            "blue": 0x0000FF,
            "orange": 0xF47B4F,
            "pink": 0xFFC0CB,
            "purple": 0x800080,
        }
        if color in colors:
            intcolor = colors[color]
            color = str(hex(colors[color]))
        else:
            await ctx.respond(
                "You need to give me either a hex code for a color or basic color name!\n"
                + "Valid colors are as follows: red, green, blue, orange, pink and purple.",
                ephemeral=True,
            )
            return
    if intcolor == 0:
        await ctx.respond("You cannot set your color to pure black.", ephemeral=True)
        return

    for role in ctx.author.roles:
        if role.color.value != 0:
            await ctx.author.remove_roles(role)
    roles = await ctx.guild.fetch_roles()
    for role in roles:
        if role.name == color.lstrip("0x").upper():
            await ctx.author.add_roles(role)
            await ctx.respond("Sounds good to me! Role added!", ephemeral=True)
            break
    else:
        role = await ctx.guild.create_role(
            name=color.lstrip("0x").upper(), color=intcolor
        )
        await ctx.author.add_roles(role)
        await ctx.respond("Sounds good to me! Role created and added!", ephemeral=True)


# admin commands


@bot.slash_command(description="owner only command")
async def senddm(ctx: SlashContext, user: discord.User, message: str):
    info = await bot.application_info()
    if ctx.author == info.owner:
        await user.send(message)
        await ctx.respond(f'Sent "{message}" to {user.mention}!', ephemeral=True)
    else:
        await ctx.respond("No.", ephemeral=True)


@bot.slash_command(description="owner only command")
async def say(ctx: SlashContext, message: str):
    info = await bot.application_info()
    if ctx.author == info.owner:
        await ctx.channel.send(message)
        await ctx.respond(f"Done!", ephemeral=True)
    else:
        await ctx.respond("No.", ephemeral=True)


@bot.slash_command(description="owner only command")
async def changestatus(ctx: SlashContext, status: str):
    info = await bot.application_info()
    if ctx.author == info.owner:
        await bot.change_presence(activity=discord.Game(name=status))
        await ctx.respond(f'Changed status to "{status}"!', ephemeral=True)
    else:
        await ctx.respond("No.", ephemeral=True)


# Global command error handler
@bot.event
async def on_application_command_error(ctx, error):
    # Check failures should be handled by the individual cogs, not here.
    if not isinstance(error, CheckFailure):
        await ctx.send(
            f"An error occured and has been automatically reported to the developer. Error: `{error}`"
        )
        info = await bot.application_info()
        sio = StringIO()
        # traceback requires a file-like object, so we use StringIO to get the traceback as a string
        traceback.print_exception(error, file=sio, limit=4)
        tb = sio.getvalue()  # get the string from the StringIO object

        if ctx.guild != None:  # if the command was run in a guild, NOT a DM
            message = f"An error occurred in {ctx.guild.name} ({ctx.guild.id}) in {ctx.channel.name} ({ctx.channel.mention}) by {ctx.author.name} ({ctx.author.mention})\n"
        else:  # command run in DM, do not include guild info
            message = f"An error occurred in A DM with {ctx.author.name} ({ctx.author.mention})\n"
        message += (
            f"Error: `{error}`\n The traceback will be supplied in the next message."
        )
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


bot.run(os.getenv("TOKEN"))
