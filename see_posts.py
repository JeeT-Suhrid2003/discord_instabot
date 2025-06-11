import os
import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv
from instagrapi import Client

# Load environment variables
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
IG_USERNAME = os.getenv("INSTA_EMAIL")
IG_PASSWORD = os.getenv("INSTA_PASSWORD")

# Discord Setup
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Instagram Client Setup
ig_client = Client()
try:
    ig_client.login(IG_USERNAME, IG_PASSWORD)
    print("Instagram client logged in successfully.")
except Exception as e:
    print(f"Failed to login Instagram client: {e}")

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"{bot.user} is online and ready!")

# Helper to create Discord embeds from Instagram media
def create_media_embeds(media):
    caption = getattr(media, 'caption_text', 'No caption')
    base_url = f"https://www.instagram.com/p/{media.code}/"
    embeds = []

    if media.media_type == 8 and hasattr(media, 'resources'):  # Album
        for resource in media.resources:
            embed = discord.Embed(description=caption)
            embed.set_image(url=resource.thumbnail_url)
            embed.add_field(name="Instagram", value=base_url, inline=False)
            embeds.append(embed)
    else:
        embed = discord.Embed(description=caption)
        embed.set_image(url=media.thumbnail_url)
        if media.media_type == 2 and getattr(media, 'video_url', None):
            embed.add_field(name="Video", value="(Video in Instagram post)", inline=False)
        embed.add_field(name="Instagram", value=base_url, inline=False)
        embeds.append(embed)

    return embeds

# Slash command to fetch latest Instagram posts
@bot.tree.command(name="insta_last", description="Fetch the last N posts from an Instagram user.")
@app_commands.describe(username="Instagram username", amount="Number of posts to fetch")
async def insta_last(interaction: discord.Interaction, username: str, amount: int):
    await interaction.response.defer()
    try:
        user_id = ig_client.user_id_from_username(username)
        medias = ig_client.user_medias(user_id, amount)
    except Exception as e:
        await interaction.followup.send(f"Error fetching posts for `{username}`: {e}")
        return

    if not medias:
        await interaction.followup.send(f"No posts found for user `{username}`.")
        return

    for media in medias:
        embeds = create_media_embeds(media)
        for embed in embeds:
            await interaction.followup.send(embed=embed)

bot.run(TOKEN)
