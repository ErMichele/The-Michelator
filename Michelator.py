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

# Directory for server configuration files
CONFIG_DIR = "server_configs"

# Ensure the directory exists
if not os.path.exists(CONFIG_DIR):
    os.makedirs(CONFIG_DIR)

# Load birthdays data (shared across servers)
with open('Compleanni_OncePice.json', 'r') as f:
    birthday_data = json.load(f)

def get_todays_birthdays():
    today = datetime.now().strftime('%d-%m')
    return birthday_data.get(today, [])

# Function to load configuration for a specific server (guild)
def load_config(guild_id):
    config_path = os.path.join(CONFIG_DIR, f"{guild_id}.json")
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            print(f"[Errore] Il file di configurazione per il server {guild_id} è corrotto.")
    # Default configuration if the file doesn't exist
    return {"OncePice": {"birthday_channel": None, "Time": [6, 30], "Active": True}}

# Function to save configuration for a specific server (guild)
def save_config(guild_id, config):
    config_path = os.path.join(CONFIG_DIR, f"{guild_id}.json")
    try:
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=4)
    except Exception as e:
        print(f"[Errore] Impossibile salvare la configurazione per il server {guild_id}: {e}")

# Function to get the configuration for a specific server
def get_server_config(guild_id):
    config = load_config(guild_id)
    return config["OncePice"]

# Function to update a specific setting for a server
def update_server_config(guild_id, key, value):
    config = load_config(guild_id)
    if "OncePice" not in config:
        config["OncePice"] = {"birthday_channel": None, "Time": [6, 30], "Active": True}
    config["OncePice"][key] = value
    save_config(guild_id, config)

@bot.event
async def on_ready():
    print(f'Siamo online come {bot.user}')
    send_daily_birthdays.start()

@bot.command()
@commands.has_permissions(administrator=True)
async def set_channel(ctx, channel: discord.TextChannel):
    update_server_config(ctx.guild.id, "birthday_channel", channel.id)
    await ctx.send(f'Canale configurato correttamente: {channel.mention}')

@bot.command()
@commands.has_permissions(administrator=True)
async def set_time(ctx, hour: int, minute: int):
    update_server_config(ctx.guild.id, "Time", [hour, minute])
    await ctx.send(f'Ora configurata correttamente: {hour:02d}:{minute:02d}')

@bot.command()
@commands.has_permissions(administrator=True)
async def toggle_active(ctx, state: bool):
    update_server_config(ctx.guild.id, "Active", state)
    status = "attivata" if state else "disattivata"
    await ctx.send(f'La funzione è stata {status}.')

@tasks.loop(minutes=1)
async def send_daily_birthdays():
    now = datetime.now()
    for config_file in os.listdir(CONFIG_DIR):
        try:
            guild_id = config_file.replace(".json", "")
            config = load_config(guild_id)
            once_pice = config["OncePice"]

            if not once_pice.get("Active", True):
                continue

            channel_id = once_pice.get("birthday_channel")
            if not channel_id:
                print(f"[Errore] Nessun canale configurato per il server {guild_id}.")
                continue

            channel = bot.get_channel(int(channel_id))
            if not channel:
                print(f"[Errore] Il canale configurato per il server {guild_id} non è valido.")
                continue

            hour, minute = once_pice.get("Time", [6, 30])
            scheduled_time = datetime(now.year, now.month, now.day, hour, minute)
            if now >= scheduled_time and (now - scheduled_time).seconds < 60:
                print("[Debbug] Printare i compleanni")
                bdays = get_todays_birthdays()
                if bdays:
                    await channel.send(f'Buongiorno! Oggi è il compleanno di: {", ".join(bdays)}')
                else:
                    await channel.send('Oggi non ci sono compleanni.')
        except Exception as e:
            print(f"[Errore] Problema nel server {guild_id}: {e}")

@send_daily_birthdays.before_loop
async def before_loop():
    await bot.wait_until_ready()

@bot.command()
async def birthdays(ctx, date: str):
    bdays = birthday_data.get(date, [])
    if bdays:
        await ctx.send(f'I compleanni del {date} sono: {", ".join(bdays)}')
    else:
        await ctx.send(f'Non ci sono compleanni il {date}')

# Load token and run the bot
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