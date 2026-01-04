import discord
from discord import app_commands
from discord.ext import tasks
import os
from dotenv import load_dotenv
import scraper
import database
import asyncio
import json

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

MY_GUILD = discord.Object(id=0) 

FILTERS_CONFIG = {
    "agreement": {
        "label": "Typ umowy",
        "options": [
            ("Umowa o pracę", "part"),
            ("Umowa zlecenie", "zlecenie"),
            ("Umowa o dzieło", "contract"),
            ("Praktyka / Staż", "practice"),
        ]
    },
    "type": {
        "label": "Wymiar pracy",
        "options": [
            ("Pełny etat", "fulltime"),
            ("Część etatu", "parttime"),
            ("Praca dodatkowa", "halftime"),
        ]
    },
    "availability":{
        "label": "Dostępność",
        "options": [
            ("Praca zmianowa", "shift_work"),
            ("Praca w weekendy", "weekends_work"),
            ("Elastyczny czas pracy", "flexible_work"),
        ]
    },
    "experience":{
        "label": "Doświadczenie",
        "options": [
            ("Wymagane doświadczenie", "exp_yes"),
            ("Bez doświadczenia", "exp_no"),
        ]
    },
}

class FilterSelect(discord.ui.Select):
    def __init__(self, key, config):
        options = [discord.SelectOption(label=l, value=v) for l, v in config["options"]]
        # Remove "Any" to simplify multi-select logic (deselecting all = any)
        # Or keep it but handle exclusively? 
        # For multi-select, usually you just select what you want.
        
        super().__init__(
            placeholder=config["label"], 
            min_values=0, 
            max_values=len(options), 
            options=options
        )
        self.key = key

    async def callback(self, interaction: discord.Interaction):
        if not self.values:
            self.view.filters.pop(self.key, None)
        else:
            self.view.filters[self.key] = self.values
        
        # Atomic update using response.edit_message to avoid 404 on ephemeral
        await interaction.response.edit_message(embed=self.view.build_embed())

class SetupWizard(discord.ui.View):
    def __init__(self, city, query, user_id):
        super().__init__()
        self.city = city
        self.query = query
        self.user_id = user_id
        self.filters = {}
        self.setup_finished = False

        # Add selects
        for key, config in FILTERS_CONFIG.items():
            self.add_item(FilterSelect(key, config))

    def build_embed(self):
        desc = f"City: **{self.city}**\nQuery: **{self.query}**\n\n**Current Filters:**\n"
        if not self.filters:
            desc += "None (All jobs)"
        else:
            for k, v in self.filters.items():
                val_str = str(v)
                if isinstance(v, list):
                   val_str = ", ".join(v)
                desc += f"- {k}: {val_str}\n"
        
        url = scraper.build_olx_url(self.city, self.query, filters=self.filters)
        desc += f"\n\n[Preview Link]({url})"
        return discord.Embed(title="Job Search Setup", description=desc, color=0x3498db)

    @discord.ui.button(label="Finish & Save", style=discord.ButtonStyle.green, row=4)
    async def finish(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.setup_finished = True
        self.stop()
        
        url = scraper.build_olx_url(self.city, self.query, filters=self.filters)
        
         # Check/Create Channel
        user_searches = await database.get_user_searches(self.user_id)
        channel_id = None
        if user_searches:
            channel_id = user_searches[0]['channel_id']
            # Verify existence
            if not interaction.client.get_channel(channel_id):
                channel_id = None

        if not channel_id:
            guild = interaction.guild
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(read_messages=False),
                interaction.user: discord.PermissionOverwrite(read_messages=True),
                guild.me: discord.PermissionOverwrite(read_messages=True)
            }
            channel = await guild.create_text_channel(f"jobs-{interaction.user.name}", overwrites=overwrites)
            channel_id = channel.id

        await database.add_search(self.user_id, channel_id, url, self.city, self.query, "praca", json.dumps(self.filters))
        await interaction.response.send_message(f"Search saved! Check <#{channel_id}>.", ephemeral=True)

from discord.ext import commands

class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=discord.Intents.all())

    async def setup_hook(self):
        await database.init_db()
        self.bg_task.start()
        
    async def check_jobs(self):
        print("Checking jobs...")
        try:
            searches = await database.get_searches()
            for search in searches:
                channel = self.get_channel(search['channel_id'])
                if not channel: continue
                
                offers = scraper.fetch_offers(search['url'])
                
                count = 0
                for offer in offers:
                    if not await database.offer_exists(offer['id']):
                        await database.add_offer(offer['id'], search['id'], offer['title'], offer['price'], offer['url'])
                        
                        embed = discord.Embed(title=offer['title'], url=offer['url'], color=0x00ff00)
                        embed.add_field(name="💰 Price", value=offer['price'], inline=True)
                        if offer.get('location'):
                            embed.add_field(name="📍 Location", value=offer['location'], inline=True)
                        if offer.get('contract') and offer['contract'] != 'N/A':
                             embed.add_field(name="📝 Contract", value=offer['contract'], inline=True)
                        if offer.get('work_load') and offer['work_load'] != 'N/A':
                             embed.add_field(name="⏰ Work Load", value=offer['work_load'], inline=True)

                        embed.set_footer(text=f"Search: {search['query']}")
                        await channel.send(f"<@{search['user_id']}> New Offer!", embed=embed)
                        count += 1
                        await asyncio.sleep(1) 
                
                if count > 0:
                    print(f"Sent {count} offers for search {search['id']}")
                    
                await asyncio.sleep(2) # Delay between searches
        except Exception as e:
            print(f"Error in check logic: {e}")

    @tasks.loop(minutes=10)
    async def bg_task(self):
        await self.wait_until_ready()
        await self.check_jobs()

    @bg_task.before_loop
    async def before_bg_task(self):
        await self.wait_until_ready()

client = MyBot()

@client.command()
async def check(ctx):
    """Force run the job check immediately."""
    await ctx.send("🔍 Checking for new jobs manually...")
    await client.check_jobs()
    await ctx.send("✅ Check complete.")


@client.event
async def on_ready():
    print(f'Logged in as {client.user} (ID: {client.user.id})')

@client.command()
async def sync(ctx):
    """Syncs slash commands to the current guild."""
    print("Syncing commands...")
    # Sync to the guild where the command was run (instant)
    client.tree.copy_global_to(guild=ctx.guild)
    await client.tree.sync(guild=ctx.guild)
    await ctx.send("Slash commands synced to this server! You might need to restart your Discord client (Ctrl+R) if they don't appear immediately.")

@client.tree.command(name="findjob", description="Start monitoring OLX for jobs")
@app_commands.describe(city="City name", query="Job title/keyword")
async def findjob(interaction: discord.Interaction, city: str, query: str):
    view = SetupWizard(city, query, interaction.user.id)
    await interaction.response.send_message(embed=view.build_embed(), view=view, ephemeral=True)

@client.tree.command(name="listjobs", description="List your active searches")
async def listjobs(interaction: discord.Interaction):
    searches = await database.get_user_searches(interaction.user.id)
    if not searches:
        await interaction.response.send_message("No active searches.", ephemeral=True)
        return
        
    msg = "**Active Searches:**\n"
    for s in searches:
        # Parse filters
        filters_str = ""
        if s['filters']:
            try:
                f_dict = json.loads(s['filters'])
                readable_filters = []
                
                for key, val_or_list in f_dict.items():
                    # Find config for this key
                    config = FILTERS_CONFIG.get(key)
                    if not config:
                        readable_filters.append(f"{key}: {val_or_list}")
                        continue
                    
                    # Helper to find label for a value
                    def get_label(v):
                        for label, value in config['options']:
                            if value == v:
                                return label
                        return v # fallback
                    
                    # Handle list or single value
                    if isinstance(val_or_list, list):
                        labels = [get_label(v) for v in val_or_list]
                        readable_value = ", ".join(labels)
                    else:
                        readable_value = get_label(val_or_list)
                        
                    readable_filters.append(f"**{config['label']}**: {readable_value}")
                
                filters_str = " | ".join(readable_filters)
            except json.JSONDecodeError:
                filters_str = "Error parsing filters"
        else:
            filters_str = "No filters"

        msg += f"🆔 **{s['id']}** | 🔍 `{s['query']}` in `{s['city']}`\n"
        msg += f"   filters: {filters_str}\n" 
    
    await interaction.response.send_message(msg, ephemeral=True)

@client.tree.command(name="stopjob", description="Stop a search by ID")
async def stopjob(interaction: discord.Interaction, search_id: int):
    await database.remove_search(search_id, interaction.user.id)
    await interaction.response.send_message(f"Search {search_id} removed.", ephemeral=True)

if __name__ == "__main__":
    if not TOKEN or TOKEN == "your_token_here":
        print("ERROR: Please set DISCORD_TOKEN in .env")
    else:
        client.run(TOKEN)
