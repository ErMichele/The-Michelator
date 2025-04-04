import discord
from discord.ext import commands, tasks
import json
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
import asyncio

intents = discord.Intents.default()
intents.message_content = True
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

@tasks.loop(minutes=1)  # Controllo più frequente per gestire cambi di orario
async def send_daily_birthdays():
    now = datetime.now()
    for guild_id, guild_data in config.items():
        try:
            once_pice = guild_data["OncePice"]
            if not once_pice.get("Active", True):  # Verifica se la funzione è attiva
                continue

            channel_id = once_pice.get("birthday_channel")
            if not channel_id:
                print(f"[Errore] Nessun canale configurato per il server {guild_id}.")
                continue

            channel = bot.get_channel(channel_id)
            if not channel:
                print(f"[Errore] Il canale configurato per il server {guild_id} non è valido.")
                continue

            # Ottieni l'orario configurato per il server
            hour, minute = once_pice.get("Time", [6, 30])
            scheduled_time = datetime(now.year, now.month, now.day, hour, minute)

            # Controlla se l'orario configurato corrisponde all'attuale momento
            if now >= scheduled_time and (now - scheduled_time).seconds < 60:  # Tolleranza di 1 minuto
                bdays = get_todays_birthdays()
                if bdays:
                    await channel.send(f'Buongiorno! Oggi è il compleanno di: {", ".join(bdays)}')
                else:
                    await channel.send('Oggi non ci sono compleanni.')
                print(f"[Log] Messaggio inviato per il server {guild_id}.")
        except Exception as e:
            print(f"[Errore] Problema nel server {guild_id}: {e}")

# Evento per avviare il ciclo
@send_daily_birthdays.before_loop
async def before_loop():
    await bot.wait_until_ready()
    print("[Log] Il ciclo è pronto per essere avviato.")

# Comando per ottenere i compleanni di una data specifica
@bot.command()
async def birthdays(ctx, date: str):
    bdays = birthday_data.get(date, [])
    if bdays:
        await ctx.send(f'I compleanni del {date} sono: {", ".join(bdays)}')
    else:
        await ctx.send(f'Non ci sono compleanni il {date}')

# Esegui il bot
load_dotenv(dotenv_path=".venv/.env")
token = os.getenv("DISCORD_BOT_TOKEN")

if not token:
    print("Errore: il token non è stato trovato.")
else:
    print("Token trovato, avvio del bot...")
    try:
        bot.run(token)
    except discord.errors.LoginFailure:
        print("Errore: token non valido. Verifica di usare il token corretto.")
