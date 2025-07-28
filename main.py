import discord
import requests
import asyncio
from bs4 import BeautifulSoup
from datetime import datetime
import os

# === CONFIGURACIÓN ===
TOKEN = os.getenv("TOKEN")  # TOKEN desde variables de entorno (Railway)
CANAL_ID = 1324168783329497151
GREMIO = "Mono Con Navaja"
INTERVALO_MINUTOS = 5

intents = discord.Intents.default()
client = discord.Client(intents=intents)
batallas_ya_publicadas = set()

async def buscar_batallas():
    await client.wait_until_ready()
    canal = client.get_channel(CANAL_ID)

    while not client.is_closed():
        try:
            url = "https://albionbb.com/battles"
            response = requests.get(url)
            soup = BeautifulSoup(response.text, "html.parser")
            enlaces = soup.select("a[href^='/battles/']")
            nuevas_urls = ["https://albionbb.com" + a["href"] for a in enlaces[:10]]

            for link in nuevas_urls:
                if link in batallas_ya_publicadas:
                    continue

                res = requests.get(link)
                html = BeautifulSoup(res.text, "html.parser")
                nombre_gremios = html.select("div.flex.flex-wrap.items-center.justify-start.text-sm a")
                if not any(GREMIO.lower() in g.text.strip().lower() for g in nombre_gremios):
                    continue

                tablas = html.select("div.flex.flex-col.rounded.border.border-gray-200.bg-white.shadow")
                datos_gremio = None
                for tabla in tablas:
                    if GREMIO.lower() in tabla.text.lower():
                        datos_gremio = tabla
                        break

                if not datos_gremio:
                    continue

                texto = datos_gremio.get_text()
                kills = extraer_valor(texto, "Kills")
                deaths = extraer_valor(texto, "Deaths")
                fama = extraer_valor(texto, "Fame")
                fecha_actual = datetime.utcnow().strftime("%d/%m/%Y - %H:%M UTC")

                embed = discord.Embed(
                    title=f"⚔️ Batalla de {GREMIO}",
                    url=link,
                    description=f"**Nueva batalla detectada**",
                    color=discord.Color.red()
                )
                embed.add_field(name="🔪 Kills", value=kills or "0", inline=True)
                embed.add_field(name="💀 Deaths", value=deaths or "0", inline=True)
                embed.add_field(name="📈 Fame", value=fama or "0", inline=True)
                embed.set_footer(text=f"⏱️ {fecha_actual}")

                await canal.send(embed=embed)
                batallas_ya_publicadas.add(link)

        except Exception as e:
            print(f"[ERROR] {e}")

        await asyncio.sleep(INTERVALO_MINUTOS * 60)

def extraer_valor(texto, campo):
    try:
        for linea in texto.splitlines():
            if campo in linea:
                return linea.split(":")[1].strip()
    except:
        return "0"

@client.event
async def on_ready():
    print(f"✅ Bot conectado como {client.user}")
    canal = client.get_channel(CANAL_ID)
    if canal:
        asyncio.create_task(canal.send("🤖 **Bot activado y escuchando batallas de Mono Con Navaja**"))

@client.event
async def setup_hook():
    client.loop.create_task(buscar_batallas())

client.run(TOKEN)