import discord
from discord.ext import commands, tasks
import aiohttp
from datetime import datetime, timezone

# ============================================
# CONFIGURATION - MODIFIE CES VALEURS
# ============================================
TOKEN = "MTUwNTIyNjk3MTUzNjE2Njk0Mg.Gi8eBV.Qx_bkNY1ovTvZ5N4-FLW3yTOQ3Ylk6GKO46B5Y"
CHANNEL_ID = 1505221558392586433  # ID du salon Discord où envoyer les messages
JELLYFIN_URL = "http://192.168.1.85:8096"

# Liens publics
LIENS_PUBLIC = {
    "🎬 Jellyfin": "http://82.226.41.79:8096",
    "🎥 Jellyseerr": "http://82.226.41.79:5055",
}

# Liens locaux
LIENS_LOCAL = {
    "🎬 Jellyfin": "http://192.168.1.85:8096",
    "🎥 Jellyseerr": "http://192.168.1.85:5055",
    "🎞️ Radarr": "http://192.168.1.85:7878",
    "📺 Sonarr": "http://192.168.1.85:8989",
    "🔍 Prowlarr": "http://192.168.1.85:9696",
    "⬇️ qBittorrent": "http://192.168.1.85:8081",
}

INTERVALLE = 60          # Vérification toutes les 60 secondes
INTERVALLE_NOTIF = 300   # Notification de statut toutes les 300 secondes
# ============================================

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

serveur_en_ligne = None
message_status = None


async def verifier_serveur():
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(JELLYFIN_URL, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                return resp.status < 500
    except Exception:
        return False


def embed_online():
    embed = discord.Embed(
        title="✅ Serveur Média EN LIGNE",
        color=discord.Color.green(),
        timestamp=datetime.now(timezone.utc)
    )
    liens_pub = "\n".join([f"[{nom}]({url})" for nom, url in LIENS_PUBLIC.items()])
    liens_loc = "\n".join([f"[{nom}]({url})" for nom, url in LIENS_LOCAL.items()])
    embed.add_field(name="🌍 Accès public", value=liens_pub, inline=False)
    embed.add_field(name="🏠 Accès local (WiFi)", value=liens_loc, inline=False)
    embed.set_footer(text="Dernière vérification")
    return embed


def embed_offline():
    embed = discord.Embed(
        title="❌ Serveur Média HORS LIGNE",
        description="Le serveur est actuellement inaccessible. Réessaie plus tard.",
        color=discord.Color.red(),
        timestamp=datetime.now(timezone.utc)
    )
    embed.set_footer(text="Dernière vérification")
    return embed


@tasks.loop(seconds=INTERVALLE)
async def verifier_loop():
    global serveur_en_ligne, message_status

    en_ligne = await verifier_serveur()
    channel = bot.get_channel(CHANNEL_ID)

    if channel is None:
        return

    if en_ligne != serveur_en_ligne:
        serveur_en_ligne = en_ligne
        if en_ligne:
            print(f"[{datetime.now()}] ✅ Serveur EN LIGNE")
            await channel.send("@everyone 🟢 Le serveur média vient de **passer en ligne** !")
        else:
            print(f"[{datetime.now()}] ❌ Serveur HORS LIGNE")
            await channel.send("@everyone 🔴 Le serveur média vient de **passer hors ligne** !")

    embed = embed_online() if en_ligne else embed_offline()

    if message_status:
        try:
            await message_status.edit(embed=embed)
        except discord.NotFound:
            message_status = await channel.send(embed=embed)
    else:
        async for msg in channel.history(limit=20):
            if msg.author == bot.user and msg.embeds:
                message_status = msg
                await message_status.edit(embed=embed)
                break
        else:
            message_status = await channel.send(embed=embed)


@tasks.loop(seconds=INTERVALLE_NOTIF)
async def notif_statut_loop():
    """Envoie un message de statut toutes les 300 secondes."""
    en_ligne = await verifier_serveur()
    channel = bot.get_channel(CHANNEL_ID)

    if channel is None:
        return

    embed = embed_online() if en_ligne else embed_offline()
    await channel.send(content="📊 **Rapport de statut automatique**", embed=embed)
    print(f"[{datetime.now()}] 📊 Notif statut envoyée")


@bot.event
async def on_ready():
    print(f"✅ Bot connecté en tant que {bot.user}")
    verifier_loop.start()
    notif_statut_loop.start()


@bot.command(name="statut")
async def statut(ctx):
    en_ligne = await verifier_serveur()
    embed = embed_online() if en_ligne else embed_offline()
    await ctx.send(embed=embed)


@bot.command(name="liens")
async def liens(ctx):
    embed = discord.Embed(title="🔗 Liens du serveur média", color=discord.Color.blue())
    liens_pub = "\n".join([f"[{nom}]({url})" for nom, url in LIENS_PUBLIC.items()])
    liens_loc = "\n".join([f"[{nom}]({url})" for nom, url in LIENS_LOCAL.items()])
    embed.add_field(name="🌍 Accès public", value=liens_pub, inline=False)
    embed.add_field(name="🏠 Accès local (WiFi)", value=liens_loc, inline=False)
    await ctx.send(embed=embed)


bot.run(TOKEN)
