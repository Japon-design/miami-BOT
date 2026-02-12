import discord
from discord import app_commands
from discord.ext import commands
import json
import os
import random
from datetime import datetime, timedelta

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix='!', intents=intents)

DATA_FILE = 'economy.json'
ROLE_INCOME_FILE = 'role_income.json'
SHOP_FILE = 'shop_items.json'

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4)

data = load_data()

def load_role_income():
    if os.path.exists(ROLE_INCOME_FILE):
        with open(ROLE_INCOME_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_role_income(d):
    with open(ROLE_INCOME_FILE, 'w') as f:
        json.dump(d, f, indent=4)

role_income_data = load_role_income()

def load_shop():
    if os.path.exists(SHOP_FILE):
        with open(SHOP_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_shop(d):
    with open(SHOP_FILE, 'w') as f:
        json.dump(d, f, indent=4)

shop_data = load_shop()

def get_user(guild_id, user_id):
    guild_str = str(guild_id)
    user_str = str(user_id)
    if guild_str not in data:
        data[guild_str] = {}
    if user_str not in data[guild_str]:
        data[guild_str][user_str] = {
            'cash': 1000,
            'bank': 0,
            'last_work': None,
            'last_crime': None,
            'last_rob': None,
            'last_daily': None,
            'last_collect': None,
            'inventory': {}
        }
    return data[guild_str][user_str]

def get_role_income(guild_id):
    guild_str = str(guild_id)
    if guild_str not in role_income_data:
        role_income_data[guild_str] = {}
    return role_income_data[guild_str]

def get_shop(guild_id):
    guild_str = str(guild_id)
    if guild_str not in shop_data:
        shop_data[guild_str] = {}
    return shop_data[guild_str]

@bot.event
async def on_ready():
    print(f'Bot conectado como {bot.user}')
    try:
        synced = await bot.tree.sync()
        print(f'Sincronizados {len(synced)} comandos.')
    except Exception as e:
        print(e)

@bot.tree.command(name="balance", description="Mira tu dinero en Liberty County")
async def balance(interaction: discord.Interaction):
    user = get_user(interaction.guild_id, interaction.user.id)
    cash = user['cash']
    bank = user['bank']
    total = cash + bank
    embed = discord.Embed(title=f"💰 Balance de {interaction.user.name} - Liberty County", color=0x00ff88)
    embed.add_field(name="Cash en mano", value=f"${cash:,}", inline=True)
    embed.add_field(name="Banco", value=f"${bank:,}", inline=True)
    embed.add_field(name="Patrimonio total", value=f"${total:,}", inline=False)
    embed.set_footer(text="Miami Roleplay Economy 🌴")
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="deposit", description="Deposita dinero al banco")
@app_commands.describe(amount="Cantidad a depositar (o 'all')")
async def deposit(interaction: discord.Interaction, amount: str):
    user = get_user(interaction.guild_id, interaction.user.id)
    if amount.lower() == 'all':
        amt = user['cash']
    else:
        try:
            amt = int(amount)
        except:
            await interaction.response.send_message("Cantidad inválida.", ephemeral=True)
            return
    if amt > user['cash'] or amt <= 0:
        await interaction.response.send_message("No tienes suficiente cash.", ephemeral=True)
        return
    user['cash'] -= amt
    user['bank'] += amt
    save_data(data)
    await interaction.response.send_message(f"Depositaste **${amt:,}** al banco. Nuevo bank: **${user['bank']:,}**")

@bot.tree.command(name="withdraw", description="Retira dinero del banco")
@app_commands.describe(amount="Cantidad a retirar (o 'all')")
async def withdraw(interaction: discord.Interaction, amount: str):
    user = get_user(interaction.guild_id, interaction.user.id)
    if amount.lower() == 'all':
        amt = user['bank']
    else:
        try:
            amt = int(amount)
        except:
            await interaction.response.send_message("Cantidad inválida.", ephemeral=True)
            return
    if amt > user['bank'] or amt <= 0:
        await interaction.response.send_message("No tienes suficiente en el banco.", ephemeral=True)
        return
    user['bank'] -= amt
    user['cash'] += amt
    save_data(data)
    await interaction.response.send_message(f"Retiraste **${amt:,}** del banco. Nuevo cash: **${user['cash']:,}**")

@bot.tree.command(name="work", description="Trabaja para ganar dinero (cada 1 hora)")
async def work(interaction: discord.Interaction):
    user = get_user(interaction.guild_id, interaction.user.id)
    now = datetime.utcnow()
    if user['last_work']:
        last = datetime.fromisoformat(user['last_work'])
        if now - last < timedelta(hours=1):
            remaining = (timedelta(hours=1) - (now - last)).seconds // 60
            await interaction.response.send_message(f"Espera **{remaining} minutos** para trabajar de nuevo.", ephemeral=True)
            return
    amount = random.randint(50, 200)
    user['cash'] += amount
    user['last_work'] = now.isoformat()
    save_data(data)
    await interaction.response.send_message(f"Trabajaste en las calles de Miami y ganaste **${amount}**! Cash: **${user['cash']:,}**")

# Agrega aquí los demás comandos que quieras (crime, rob, daily, pay, leaderboard, set-role-income, collect, shop, buy, inventory)
# Si necesitas que te los vuelva a pegar todos juntos dime y lo hago en un solo bloque.

bot.run(os.getenv('MTQ3MTU2MTY2NjQxMDk3NTMwNA.Gt9ItR.YWI3l_bNut0X105FGkuIlGWenJ6nDkan5wtF50'))
