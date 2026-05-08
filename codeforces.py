import requests
from datetime import datetime, timedelta, timezone


def get_user_info(handle):
    try:
        r = requests.get(f"https://codeforces.com/api/user.info?handles={handle}", timeout=10)
        data = r.json()
        if data["status"] == "OK":
            return data["result"][0]
    except Exception as e:
        print(f"Error fetching info for {handle}: {e}")
    return None


def get_solved_count(handle, days):
    try:
        r = requests.get(f"https://codeforces.com/api/user.status?handle={handle}", timeout=10)
        data = r.json()
        if data["status"] != "OK":
            return 0
        subs = data["result"]
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        solved = set()
        for s in subs:
            if s["verdict"] == "OK":
                sub_time = datetime.fromtimestamp(s["creationTimeSeconds"], tz=timezone.utc)
                if sub_time >= cutoff:
                    solved.add((s["problem"]["contestId"], s["problem"]["index"]))
        return len(solved)
    except Exception as e:
        print(f"Error fetching submissions for {handle}: {e}")
        return 0


def handle_exists(handle):
    info = get_user_info(handle)
    return info is not None


def get_rank_emoji(rank):
    if not rank:
        return "⬜"
    rank = rank.lower()
    if "legendary" in rank:
        return "🔴"
    elif "international" in rank and "grandmaster" in rank:
        return "🔴"
    elif "grandmaster" in rank:
        return "🔴"
    elif "master" in rank:
        return "🟠"
    elif "candidate" in rank:
        return "🟣"
    elif "expert" in rank:
        return "🔵"
    elif "specialist" in rank:
        return "🩵"
    elif "pupil" in rank:
        return "🟢"
    else:
        return "⬜"


def build_embed(handle, info, daily, weekly):
    import discord
    rating = info.get("rating", None)
    rank = info.get("rank", "Unrated")
    max_rating = info.get("maxRating", "N/A")
    emoji = get_rank_emoji(rank)

    embed = discord.Embed(
        title=f"{emoji} {handle}",
        url=f"https://codeforces.com/profile/{handle}",
        color=0x5865F2
    )
    embed.add_field(name="⭐ Current Rating", value=f"**{rating if rating else 'Unrated'}** ({rank})", inline=False)
    embed.add_field(name="📈 Max Rating", value=f"**{max_rating}**", inline=True)
    embed.add_field(name="✅ Solved Today", value=f"**{daily}** problems", inline=True)
    embed.add_field(name="📅 Solved This Week", value=f"**{weekly}** problems", inline=True)
    embed.set_footer(text=f"Generated at {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    return embed
