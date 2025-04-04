import discord
from discord.ext import commands, tasks
import json
from datetime import datetime, timedelta
import os
import asyncio

# Creare gli intents
intents = discord.Intents.default()
intents.message_content = True  # Necessario per leggere il contenuto dei messaggi

# Creare il bot
bot = commands.Bot(command_prefix='!', intents=intents)

# Funzioni per caricare e salvare le configurazioni
def load_config():
    if os.path.exists('config.json'):
        with open('config.json', 'r') as f:
            return json.load(f)
    return {}

def save_config(config):
    with open('config.json', 'w') as f:
        json.dump(config, f, indent=4)

config = load_config()

# Funzione per ottenere la configurazione di un server specifico
def get_server_config(guild_id):
    guild_id = str(guild_id)  # Converti l'ID in stringa per usarlo come chiave
    if guild_id not in config:
        config[guild_id] = {"OncePice": {"birthday_channel": None, "Time": [6, 30], "Active": True}}
        save_config(config)
    return config[guild_id]["OncePice"]

# Funzione per aggiornare la configurazione di un server specifico
def update_server_config(guild_id, key, value):
    guild_id = str(guild_id)  # Converti l'ID in stringa per usarlo come chiave
    if guild_id not in config:
        config[guild_id] = {"OncePice": {"birthday_channel": None, "Time": [6, 30], "Active": False}}
    config[guild_id]["OncePice"][key] = value
    save_config(config)

# Carica i compleanni dal file JSON
with open('Compleanni_OncePice.json', 'r') as f:
    birthday_data = json.load(f)

# Funzione per ottenere i compleanni del giorno
def get_todays_birthdays():
    today = datetime.now().strftime('%d-%m')
    return birthday_data.get(today, [])

# Evento che viene eseguito quando il bot è pronto
@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')

# Comando per configurare il canale in cui inviare i messaggi di compleanno
@bot.command()
@commands.has_permissions(administrator=True)  # Solo amministratori possono configurare
async def set_channel(ctx, channel: discord.TextChannel):
    update_server_config(ctx.guild.id, "birthday_channel", channel.id)
    await ctx.send(f'Canale configurato correttamente: {channel.mention}')

# Comando per configurare l'orario dei messaggi
@bot.command()
@commands.has_permissions(administrator=True)
async def set_time(ctx, hour: int, minute: int):
    update_server_config(ctx.guild.id, "Time", [hour, minute])
    await ctx.send(f'Ora configurata correttamente: {hour:02d}:{minute:02d}')

# Comando per attivare o disattivare la funzione
@bot.command()
@commands.has_permissions(administrator=True)
async def toggle_active(ctx, state: bool):
    update_server_config(ctx.guild.id, "Active", state)
    status = "attivata" if state else "disattivata"
    await ctx.send(f'La funzione è stata {status}.')

# Attività programmata per inviare i compleanni
@tasks.loop(hours=24)
async def send_daily_birthdays():
    for guild_id, guild_data in config.items():
        once_pice = guild_data["OncePice"]
        if once_pice.get("Active", True):
            channel_id = once_pice.get("birthday_channel")
            if channel_id is None:
                print(f"Nessun canale configurato per il server {guild_id}.")
                continue

            channel = bot.get_channel(channel_id)
            if channel is None:
                print(f"Il canale configurato per il server {guild_id} non è valido.")
                continue

            bdays = get_todays_birthdays()
            if bdays:
                await channel.send(f'Buongiorno! Oggi è il compleanno di: {", ".join(bdays)}')
            else:
                await channel.send('Oggi non ci sono compleanni.')

# Avvia il loop alle impostazioni dell'orario
@send_daily_birthdays.before_loop
async def before():
    await bot.wait_until_ready()
    now = datetime.now()
    for guild_id, guild_data in config.items():
        once_pice = guild_data["OncePice"]
        hour, minute = once_pice.get("Time", [6, 30])
        future = datetime(now.year, now.month, now.day, hour, minute)
        if now >= future:
            future += timedelta(days=1)
        delay = (future - now).total_seconds()
        await asyncio.sleep(delay)

# Esegui il bot
bot.run('MTM0MzkzNTM0MDM4MDk1MDYwOA.GdWz2k.cBiZZpT4qxmKUHRMfCkUUN4NT7f3jNBux0ujCg')
