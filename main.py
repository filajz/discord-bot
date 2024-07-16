import discord
from discord import app_commands
import os
import asyncio

intents = discord.Intents.default()
intents.messages = True

class MyClient(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tree = app_commands.CommandTree(self)
        self.reminders = {}
        self.reminder_settings = {}

    async def setup_hook(self):
        await self.tree.sync()

client = MyClient(intents=intents)

@client.event
async def on_ready():
    print(f'Přihlášen jako {client.user}')
    print("Příkazy synchronizovány.")

class ReminderView(discord.ui.View):
    def __init__(self, user_id: int, seconds: int, message: str):
        super().__init__(timeout=None)
        self.user_id = user_id
        self.seconds = seconds
        self.message = message

    @discord.ui.button(label="Pozastavit", style=discord.ButtonStyle.danger)
    async def stop_reminder(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("Nemůžeš pozastavit cizí připomínku!", ephemeral=True)
            return

        if self.user_id in client.reminders:
            client.reminders[self.user_id].cancel()
            del client.reminders[self.user_id]
            await interaction.response.send_message("Tvoje připomínka byla pozastavena.", ephemeral=True)
        else:
            await interaction.response.send_message("Nemáš žádné probíhající připomínky.", ephemeral=True)

    @discord.ui.button(label="Pokračovat", style=discord.ButtonStyle.success)
    async def start_reminder(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("Nemůžeš obnovit cizí připomínku!", ephemeral=True)
            return

        if self.user_id in client.reminders:
            await interaction.response.send_message("Již máš probíhající připomínku.", ephemeral=True)
            return

        async def reminder_task():
            while True:
                await asyncio.sleep(self.seconds)
                await interaction.channel.send(f"{interaction.user.mention} {self.message}")

        task = client.loop.create_task(reminder_task())
        client.reminders[self.user_id] = task
        await interaction.response.send_message("Připomínka bude opět pokračovat.", ephemeral=True)

@client.tree.command(name="remindme", description="Nastaví připomínku dle zvoleného intervalu s možností nastavit vlastní zprávu")
@app_commands.describe(
    value="Počet zvolených jednotek intervalu",
    unit="Jednotka času (seconds, minutes, nebo hours)",
    message="Vlastní zpráva (nepovinné)"
)
async def remindme(interaction: discord.Interaction, value: int, unit: str, message: str = "Tvoje připomínka!"):
    user_id = interaction.user.id

    # Convert unit to seconds
    if unit.lower() == "seconds":
        seconds = value
    elif unit.lower() == "minutes":
        seconds = value * 60
    elif unit.lower() == "hours":
        seconds = value * 3600
    else:
        await interaction.response.send_message("Nesprávná jednotka času! Prosím používej 'seconds', 'minutes', nebo 'hours'.", ephemeral=True)
        return

    if user_id in client.reminders:
        client.reminders[user_id].cancel()

    async def reminder_task():
        while True:
            await asyncio.sleep(seconds)
            await interaction.channel.send(f"{interaction.user.mention} {message}")

    task = client.loop.create_task(reminder_task())
    client.reminders[user_id] = task
    client.reminder_settings[user_id] = (value, unit, seconds, message)

    # Format the unit to handle singular/plural forms
    unit_display = unit[:-1]
    description = f"Připomínka nastavena pro zvolený interval – {value} {unit_display}(s) \n {message}"

    embed = discord.Embed(title="Připomínka nastavena", description=description, color=discord.Color.blue())
    view = ReminderView(user_id, seconds, message)

    await interaction.response.send_message(embed=embed, view=view)

@client.tree.command(name="clear", description="Smaže zvolený počet zpráv v dané místnosti")
async def clear(interaction: discord.Interaction, amount: int):
    await interaction.response.defer(ephemeral=True)
    deleted = await interaction.channel.purge(limit=amount)
    await interaction.followup.send(f"Smazal jsem {len(deleted)} zpráv.", ephemeral=True)

# Run the bot with the specified token
client.run(os.getenv('DISCORD_BOT_TOKEN'))
