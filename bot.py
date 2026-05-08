import os
import discord
from discord.ext import commands
from discord import app_commands
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, timezone

import db
import codeforces as cf

TOKEN = os.environ["DISCORD_TOKEN"]

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)
scheduler = AsyncIOScheduler()


# ─────────────────────────────────────────
# Report logic
# ─────────────────────────────────────────

async def send_report_to_guild(guild_id, channel_id):
    channel = await bot.fetch_channel(channel_id)
    if not channel:
        return

    handles = db.get_handles(guild_id)
    if not handles:
        await channel.send("⚠️ No handles are being tracked. Use `/add <handle>` to add one.")
        return

    await channel.send("📬 **Daily Codeforces Report**")
    for handle in handles:
        info = cf.get_user_info(handle)
        if not info:
            await channel.send(f"❌ Could not fetch data for `{handle}`")
            continue
        daily = cf.get_solved_count(handle, 1)
        weekly = cf.get_solved_count(handle, 7)
        embed = cf.build_embed(handle, info, daily, weekly)
        await channel.send(embed=embed)


async def daily_job():
    now_hour = datetime.now(timezone.utc).hour
    servers = db.get_all_servers()
    for server in servers:
        if server["report_hour"] == now_hour:
            try:
                await send_report_to_guild(server["guild_id"], server["channel_id"])
            except Exception as e:
                print(f"Error sending report to guild {server['guild_id']}: {e}")


# ─────────────────────────────────────────
# Bot events
# ─────────────────────────────────────────

@bot.event
async def on_ready():
    db.init_db()
    await bot.tree.sync()
    scheduler.add_job(daily_job, "cron", minute=0)  # runs every hour, checks report_hour per server
    scheduler.start()
    print(f"✅ Logged in as {bot.user}")
    print(f"✅ Slash commands synced")
    print(f"✅ Scheduler started")


# ─────────────────────────────────────────
# /setchannel — set the report channel
# ─────────────────────────────────────────

@bot.tree.command(name="setchannel", description="Set the channel for daily CF reports")
@app_commands.checks.has_permissions(manage_guild=True)
async def slash_setchannel(interaction: discord.Interaction, channel: discord.TextChannel):
    db.set_channel(interaction.guild_id, channel.id)
    await interaction.response.send_message(f"✅ Daily reports will be sent to {channel.mention}")

@bot.command(name="setchannel")
@commands.has_permissions(manage_guild=True)
async def prefix_setchannel(ctx, channel: discord.TextChannel):
    db.set_channel(ctx.guild.id, channel.id)
    await ctx.send(f"✅ Daily reports will be sent to {channel.mention}")


# ─────────────────────────────────────────
# /settime — set the daily report hour (UTC)
# ─────────────────────────────────────────

@bot.tree.command(name="settime", description="Set the daily report hour in UTC (0-23)")
@app_commands.checks.has_permissions(manage_guild=True)
async def slash_settime(interaction: discord.Interaction, hour: int):
    if hour < 0 or hour > 23:
        await interaction.response.send_message("❌ Hour must be between 0 and 23 (UTC).")
        return
    db.set_report_hour(interaction.guild_id, hour)
    await interaction.response.send_message(f"✅ Daily report time set to **{hour:02d}:00 UTC**")

@bot.command(name="settime")
@commands.has_permissions(manage_guild=True)
async def prefix_settime(ctx, hour: int):
    if hour < 0 or hour > 23:
        await ctx.send("❌ Hour must be between 0 and 23 (UTC).")
        return
    db.set_report_hour(ctx.guild.id, hour)
    await ctx.send(f"✅ Daily report time set to **{hour:02d}:00 UTC**")


# ─────────────────────────────────────────
# /add — add a CF handle
# ─────────────────────────────────────────

@bot.tree.command(name="add", description="Add a Codeforces handle to track")
async def slash_add(interaction: discord.Interaction, handle: str):
    await interaction.response.defer()
    if not cf.handle_exists(handle):
        await interaction.followup.send(f"❌ Handle `{handle}` not found on Codeforces.")
        return
    success = db.add_handle(interaction.guild_id, handle, interaction.user.id)
    if success:
        await interaction.followup.send(f"✅ Added `{handle}` to tracking list.")
    else:
        await interaction.followup.send(f"⚠️ `{handle}` is already being tracked.")

@bot.command(name="add")
async def prefix_add(ctx, handle: str):
    async with ctx.typing():
        if not cf.handle_exists(handle):
            await ctx.send(f"❌ Handle `{handle}` not found on Codeforces.")
            return
        success = db.add_handle(ctx.guild.id, handle, ctx.author.id)
        if success:
            await ctx.send(f"✅ Added `{handle}` to tracking list.")
        else:
            await ctx.send(f"⚠️ `{handle}` is already being tracked.")


# ─────────────────────────────────────────
# /remove — remove a CF handle
# ─────────────────────────────────────────

@bot.tree.command(name="remove", description="Remove a Codeforces handle from tracking")
async def slash_remove(interaction: discord.Interaction, handle: str):
    success = db.remove_handle(interaction.guild_id, handle)
    if success:
        await interaction.response.send_message(f"✅ Removed `{handle}` from tracking list.")
    else:
        await interaction.response.send_message(f"❌ `{handle}` was not in the tracking list.")

@bot.command(name="remove")
async def prefix_remove(ctx, handle: str):
    success = db.remove_handle(ctx.guild.id, handle)
    if success:
        await ctx.send(f"✅ Removed `{handle}` from tracking list.")
    else:
        await ctx.send(f"❌ `{handle}` was not in the tracking list.")


# ─────────────────────────────────────────
# /list — list all tracked handles
# ─────────────────────────────────────────

@bot.tree.command(name="list", description="List all tracked Codeforces handles")
async def slash_list(interaction: discord.Interaction):
    handles = db.get_handles(interaction.guild_id)
    if not handles:
        await interaction.response.send_message("📭 No handles are being tracked yet. Use `/add <handle>` to add one.")
        return
    handle_list = "\n".join([f"• `{h}`" for h in handles])
    await interaction.response.send_message(f"📋 **Tracked Handles:**\n{handle_list}")

@bot.command(name="list")
async def prefix_list(ctx):
    handles = db.get_handles(ctx.guild.id)
    if not handles:
        await ctx.send("📭 No handles are being tracked yet. Use `!add <handle>` to add one.")
        return
    handle_list = "\n".join([f"• `{h}`" for h in handles])
    await ctx.send(f"📋 **Tracked Handles:**\n{handle_list}")


# ─────────────────────────────────────────
# /report — trigger an instant report
# ─────────────────────────────────────────

@bot.tree.command(name="report", description="Trigger an instant Codeforces report")
async def slash_report(interaction: discord.Interaction):
    await interaction.response.defer()
    server = db.get_server(interaction.guild_id)
    if not server or not server["channel_id"]:
        await interaction.followup.send("❌ No channel set. Use `/setchannel` first.")
        return
    await send_report_to_guild(interaction.guild_id, server["channel_id"])
    await interaction.followup.send("✅ Report sent!")

@bot.command(name="report")
async def prefix_report(ctx):
    server = db.get_server(ctx.guild.id)
    if not server or not server["channel_id"]:
        await ctx.send("❌ No channel set. Use `!setchannel #channel` first.")
        return
    await send_report_to_guild(ctx.guild.id, server["channel_id"])
    await ctx.send("✅ Report sent!")


# ─────────────────────────────────────────
# /help — show all commands
# ─────────────────────────────────────────

@bot.tree.command(name="help", description="Show all available commands")
async def slash_help(interaction: discord.Interaction):
    embed = discord.Embed(title="📖 CF Tracker Commands", color=0x5865F2)
    embed.add_field(name="/add <handle> or !add <handle>", value="Add a CF handle to track", inline=False)
    embed.add_field(name="/remove <handle> or !remove <handle>", value="Remove a CF handle", inline=False)
    embed.add_field(name="/list or !list", value="Show all tracked handles", inline=False)
    embed.add_field(name="/report or !report", value="Trigger an instant report", inline=False)
    embed.add_field(name="/setchannel #channel or !setchannel #channel", value="Set the report channel (Admin only)", inline=False)
    embed.add_field(name="/settime <hour> or !settime <hour>", value="Set daily report hour in UTC 0-23 (Admin only)", inline=False)
    await interaction.response.send_message(embed=embed)

@bot.command(name="help")
async def prefix_help(ctx):
    embed = discord.Embed(title="📖 CF Tracker Commands", color=0x5865F2)
    embed.add_field(name="/add <handle> or !add <handle>", value="Add a CF handle to track", inline=False)
    embed.add_field(name="/remove <handle> or !remove <handle>", value="Remove a CF handle", inline=False)
    embed.add_field(name="/list or !list", value="Show all tracked handles", inline=False)
    embed.add_field(name="/report or !report", value="Trigger an instant report", inline=False)
    embed.add_field(name="/setchannel #channel or !setchannel #channel", value="Set the report channel (Admin only)", inline=False)
    embed.add_field(name="/settime <hour> or !settime <hour>", value="Set daily report hour in UTC 0-23 (Admin only)", inline=False)
    await ctx.send(embed=embed)


bot.run(TOKEN)
