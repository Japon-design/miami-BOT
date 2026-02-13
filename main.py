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

# Archivos de datos
DATA_FILE = 'economy.json'
DNI_FILE = 'dni_data.json'

# Cargar / guardar balances de economía
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4)

data = load_data()

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
            'last_daily': None,
        }
    return data[guild_str][user_str]

# Cargar / guardar DNI
def load_dni():
    if os.path.exists(DNI_FILE):
        with open(DNI_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_dni(d):
    with open(DNI_FILE, 'w') as f:
        json.dump(d, f, indent=4)

dni_data = load_dni()

@bot.event
async def on_ready():
    print(f'Bot conectado como {bot.user}')
    try:
        synced = await bot.tree.sync()
        print(f'Sincronizados {len(synced)} comandos.')
    except Exception as e:
        print(e)

# ==================== COMANDOS DE ECONOMÍA ====================

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

@bot.tree.command(name="daily", description="Reclama tu recompensa diaria")
async def daily(interaction: discord.Interaction):
    user = get_user(interaction.guild_id, interaction.user.id)
    now = datetime.utcnow()
    if user['last_daily']:
        last = datetime.fromisoformat(user['last_daily'])
        if now - last < timedelta(hours=24):
            remaining = (timedelta(hours=24) - (now - last)).seconds // 3600
            await interaction.response.send_message(f"Vuelve en **{remaining} horas** para tu daily.", ephemeral=True)
            return
    amount = random.randint(500, 1200)
    user['cash'] += amount
    user['last_daily'] = now.isoformat()
    save_data(data)
    await interaction.response.send_message(f"¡Daily reclamado! Ganaste **${amount}**. Cash: **${user['cash']:,}** 🌴")

# ==================== SISTEMA DE DNI / ID CARD ====================

@bot.event
async def on_member_join(member):
    try:
        rol_sin_verificar = discord.utils.get(member.guild.roles, name="No verificado")  # Cambia el nombre si usas otro
        await member.add_roles(rol_No_verificado)
    except:
        pass

    channel = member.guild.get_channel(116879886001926176)  # Cambia por el ID real de tu canal
    if channel:
        await channel.send(f"¡Bienvenido {member.mention} a Miami Roleplay! Crea tu DNI con **/crear-dni** para acceder a el servidor.")

@bot.tree.command(name="crear-dni", description="Crea tu DNI para el roleplay (obligatorio)")
@app_commands.describe(
    nombre="Tu nombre en RP",
    apellido="Tu apellido en RP",
    edad="Tu edad en RP (número)",
    genero="Masculino / Femenino / Otro",
    nacionalidad="Tu nacionalidad (ej. Costarricense, Nicaragüense)",
    tipo_sangre="Tu tipo de sangre (ej. O+, A-, AB+)"
)
async def crear_dni(
    interaction: discord.Interaction,
    nombre: str,
    apellido: str,
    edad: int,
    genero: str,
    nacionalidad: str,
    tipo_sangre: str
):
    user_id = str(interaction.user.id)
    dni_data[user_id] = {
        "nombre": nombre,
        "apellido": apellido,
        "edad": edad,
        "genero": genero,
        "nacionalidad": nacionalidad,
        "tipo_sangre": tipo_sangre,
        "creado": datetime.utcnow().isoformat()
    }
    save_dni(dni_data)

    embed = discord.Embed(title="🆔 DNI Oficial - Miami Roleplay", color=0x00ff00)
    embed.set_thumbnail(url=interaction.user.avatar.url if interaction.user.avatar else None)
    embed.add_field(name="Nombre Completo", value=f"{nombre} {apellido}", inline=False)
    embed.add_field(name="Edad", value=str(edad), inline=True)
    embed.add_field(name="Género", value=genero, inline=True)
    embed.add_field(name="Nacionalidad", value=nacionalidad, inline=True)
    embed.add_field(name="Tipo de Sangre", value=tipo_sangre, inline=True)
    embed.add_field(name="ID Único", value=user_id[-8:], inline=True)
    embed.set_footer(text="Miami Roleplay | Verificado 🌴")

    await interaction.response.send_message(embed=embed, ephemeral=False)

    # Asigna rol verificado y quita bloqueo (cambia nombres si usas otros)
    rol_verificado = discord.utils.get(interaction.guild.roles, name="Ciudadano Verificado")
    rol_sin_verificar = discord.utils.get(interaction.guild.roles, name="Sin Verificar")
    if rol_verificado:
        await interaction.user.add_roles(_Ciudadano_de_Miami)
    if rol_sin_verificar:
        await interaction.user.remove_roles(rol_No_verificado)

    await interaction.followup.send("¡DNI creado con éxito! Ahora tienes acceso completo al servidor.", ephemeral=True)

@bot.tree.command(name="ver-mi-dni", description="Mira tu DNI oficial en Liberty County")
async def ver_mi_dni(interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    if user_id not in dni_data:
        await interaction.response.send_message("Aún no has creado tu DNI. Usa **/crear-dni** primero.", ephemeral=True)
        return

    dni = dni_data[user_id]
    embed = discord.Embed(title="🆔 Tu DNI Oficial - Miami Roleplay", color=0x00ff00)
    embed.set_thumbnail(url=interaction.user.avatar.url if interaction.user.avatar else None)
    embed.add_field(name="Nombre Completo", value=f"{dni['nombre']} {dni['apellido']}", inline=False)
    embed.add_field(name="Edad", value=str(dni['edad']), inline=True)
    embed.add_field(name="Género", value=dni['genero'], inline=True)
    embed.add_field(name="Nacionalidad", value=dni['nacionalidad'], inline=True)
    embed.add_field(name="Tipo de Sangre", value=dni['tipo_sangre'], inline=True)
    embed.add_field(name="ID Único", value=user_id[-8:], inline=True)
    embed.add_field(name="Creado el", value=dni['creado'][:10], inline=True)
    embed.set_footer(text="Miami Roleplay | Verificado 🌴")

    await interaction.response.send_message(embed=embed, ephemeral=False)

@bot.tree.command(name="editar-dni", description="Edita un campo de tu DNI")
@app_commands.describe(
    campo="Campo a cambiar: nombre, apellido, edad, genero, nacionalidad, tipo_sangre",
    valor="El nuevo valor"
)
async def editar_dni(interaction: discord.Interaction, campo: str, valor: str):
    user_id = str(interaction.user.id)
    if user_id not in dni_data:
        await interaction.response.send_message("No tienes DNI creado. Usa **/crear-dni** primero.", ephemeral=True)
        return

    campo = campo.lower()
    campos_validos = ["nombre", "apellido", "edad", "genero", "nacionalidad", "tipo_sangre"]
    if campo not in campos_validos:
        await interaction.response.send_message(f"Campo inválido. Usa: {', '.join(campos_validos)}", ephemeral=True)
        return

    if campo == "edad":
        try:
            valor = int(valor)
        except:
            await interaction.response.send_message("La edad debe ser un número.", ephemeral=True)
            return

    dni_data[user_id][campo] = valor
    save_dni(dni_data)

    await interaction.response.send_message(f"¡{campo.capitalize()} actualizado a **{valor}**! Usa **/ver-mi-dni** para ver tu DNI.", ephemeral=True

# Inicia el bot

bot.run(os.getenv('MTQ3MTU2MTY2NjQxMDk3NTMwNA.GLo8mQ.VrPOhLWSU2cfauYC1YbWjyH2HvqOXj9RyMZDsw'))
