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

# Funzioni per caricare e salvare la configurazione
def load_config():
    if os.path.exists('config.json'):
        with open('config.json', 'r') as f:
            return json.load(f)
    return {"OncePice": {"birthday_channel": None, "Time": [6, 30]}}

def save_config(config):
    with open('config.json', 'w') as f:
        json.dump(config, f, indent=4)

config = load_config()

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
    send_daily_birthdays.start()

# Comando per configurare il canale in cui inviare i messaggi di compleanno
@bot.command()
@commands.has_permissions(administrator=True)  # Solo amministratori possono configurare
async def set_channel(ctx, channel: discord.TextChannel):
    config["OncePice"]["birthday_channel"] = channel.id
    save_config(config)
    await ctx.send(f'Canale configurato correttamente: {channel.mention}')

# Comando per configurare l'orario dei messaggi
@bot.command()
@commands.has_permissions(administrator=True)
async def set_time(ctx, hour: int, minute: int):
    config["OncePice"]["Time"] = [hour, minute]
    save_config(config)
    await ctx.send(f'Ora configurata correttamente: {hour:02d}:{minute:02d}')

# Attività programmata per inviare i compleanni
@tasks.loop(hours=24)
async def send_daily_birthdays():
    channel_id = config["OncePice"].get("birthday_channel")
    if channel_id is None:
        print("Il canale non è stato configurato.")
        return

    channel = bot.get_channel(channel_id)
    if channel is None:
        print("Il canale configurato non è valido.")
        return

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
    hour, minute = config["OncePice"].get("Time", [6, 30])
    future = datetime(now.year, now.month, now.day, hour, minute)
    if now >= future:
        future += timedelta(days=1)
    delay = (future - now).total_seconds()
    await asyncio.sleep(delay)

# Esegui il bot
bot.run('INSERISCI_IL_TUO_TOKEN')
