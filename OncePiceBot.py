import discord
from discord.ext import commands, tasks
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import json
from datetime import datetime
import asyncio

bot = commands.Bot(command_prefix='!')

# Carica i compleanni dal file JSON
with open('Compleanni.json', 'r') as f:
    birthdays = json.load(f)

# Funzione per ottenere i compleanni del giorno
def get_todays_birthdays():
    today = datetime.now().strftime('%m-%d')
    return birthdays.get(today, [])

# Evento che viene eseguito quando il bot è pronto
@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')
    send_daily_birthdays.start()

# Comando per ottenere i compleanni di una data specifica
@bot.command()
async def birthdays(ctx, date: str):
    bdays = birthdays.get(date, [])
    if bdays:
        await ctx.send(f'I compleanni del {date} sono: {", ".join(bdays)}')
    else:
        await ctx.send(f'Non ci sono compleanni il {date}')

# Attività programmata per inviare i compleanni ogni giorno alle 6:30
@tasks.loop(hours=24)
async def send_daily_birthdays():
    channel = bot.get_channel(YOUR_CHANNEL_ID)
    bdays = get_todays_birthdays()
    if bdays:
        await channel.send(f'Buongiorno! Oggi è il compleanno di: {", ".join(bdays)}')
    else:
        await channel.send('Oggi non ci sono compleanni.')

# Avvia il loop alle 6:30 ogni giorno
@send_daily_birthdays.before_loop
async def before():
    await bot.wait_until_ready()
    now = datetime.now()
    future = datetime(now.year, now.month, now.day, 6, 30)
    if now >= future:
        future = future.replace(day=now.day + 1)
    delay = (future - now).total_seconds()
    await asyncio.sleep(delay)

bot.run('YOUR_BOT_TOKEN')  # Sostituisci 'YOUR_BOT_TOKEN' con il token del tuo bot
