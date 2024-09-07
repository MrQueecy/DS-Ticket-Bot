import discord
from discord.ext import commands
from discord.ui import View, Button, Modal, TextInput

intents = discord.Intents.default()
intents.typing = False
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

OPTION1_CATEGORY_ID = ID
OPTION2_CATEGORY_ID = ID
OPTION3_CATEGORY_ID = ID
OPTION4_CATEGORY_ID = ID
PANEL_CHANNEL_ID = ID
LOG_CHANNEL_ID = ID
ADMINISTRATOR_ROLE_ID = [ID, ID, ID]
SUPPORT_ROLE_ID = [ID, ID, ID]

class TicketDropdown(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Option 1", description="description 1"),
            discord.SelectOption(label="Option 2", description="description 2"),
            discord.SelectOption(label="Option 3", description="description 3"),
            discord.SelectOption(label="Option 4", description="description 4")
        ]
        super().__init__(placeholder="Select a ticket type...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        guild = interaction.guild
        member = interaction.user

        category_id = None
        welcome_message = None  

        if self.values[0] == "Option 1":
            category_id = OPTION1_CATEGORY_ID
            welcome_message = "Welcome message 1"
        elif self.values[0] == "Option 2":
            category_id = OPTION2_CATEGORY_ID
            welcome_message = "Welcome message 2"
        elif self.values[0] == "Option 3":
            category_id = OPTION3_CATEGORY_ID
            welcome_message = "Welcome message 3"
        elif self.values[0] == "Option 4":
            category_id = OPTION4_CATEGORY_ID
            welcome_message = "Welcome message 4"

        category = bot.get_channel(category_id)

        if category is None:
            await interaction.response.send_message(f'Category with ID: {category_id} not found. Ticket was not created.', ephemeral=True)
            return

        if not guild.me.guild_permissions.manage_channels:
            await interaction.response.send_message(f'I do not have permission to manage channels.', ephemeral=True)
            return

        try:
            ticket_channel = discord.utils.get(guild.channels, category_id=category_id, name=f'ticket-{member.display_name}')

            if ticket_channel:
                await ticket_channel.send(f'<@{member.id}>', embed=discord.Embed(title='Ticket Support', description=welcome_message, color=0x34c6eb))
            else:
                overwrites = {
                    guild.default_role: discord.PermissionOverwrite(read_messages=False),
                    member: discord.PermissionOverwrite(read_messages=True, send_messages=True, attach_files=True)
                }
                
                for role_id in SUPPORT_ROLE_ID:
                    support_role = guild.get_role(role_id)
                    if support_role:
                        overwrites[support_role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

                channel = await category.create_text_channel(f'ticket-{member.display_name}', overwrites=overwrites)

                embed = discord.Embed(title='Ticket Support', description=welcome_message, color=0x34c6eb)
                view = CloseTicketButton(channel, member)
                await channel.send(f'<@{member.id}> {welcome_message}', embed=embed, view=view)

                private_message = "Ticket has been created."
                await member.send(private_message)

        except discord.HTTPException as e:
            await interaction.response.send_message(f'Error: {e}', ephemeral=True)

class TicketDropdownView(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(TicketDropdown())

class TicketReasonModal(Modal):
    def __init__(self, channel, member):
        super().__init__(title="Reason for Closing the Ticket")
        self.channel = channel
        self.member = member
        self.category = self.channel.category

        self.reason_input = TextInput(
            label="Reason for Closing",
            style=discord.TextStyle.paragraph,
            placeholder="Type your reason here...",
            required=True
        )
        self.add_item(self.reason_input)

    async def on_submit(self, interaction: discord.Interaction):
        reason = self.reason_input.value
        await self.channel.send(f'Ticket was closed by {interaction.user.mention} for the reason: {reason}. Category: {self.category.name}')

        await interaction.response.send_message(f'Ticket {self.channel.name} was closed for the reason: {reason}. Category: {self.category.name}', ephemeral=True)

        try:
            await self.member.send(f'**Your ticket** "{self.channel.name}" was closed for the **reason**: {reason}. **Category**: {self.category.name}')
        except discord.Forbidden:
            print(f"Cannot send a private message to {self.member.display_name}")

        log_channel = bot.get_channel(LOG_CHANNEL_ID)
        if log_channel:
            log_embed = discord.Embed(
                title="Ticket Closed",
                description=f'Ticket "{self.channel.name}" was closed.',
                color=discord.Color.red()
            )
            log_embed.add_field(name="Ticket Creator", value=self.member.mention)
            log_embed.add_field(name="Closed by", value=interaction.user.mention)
            log_embed.add_field(name="Reason", value=reason)
            log_embed.add_field(name="Category", value=self.category.name)  
            await log_channel.send(embed=log_embed)

        await self.channel.delete()
        
class CloseTicketButton(View):
    def __init__(self, channel, member):
        super().__init__()
        self.channel = channel
        self.member = member

    @discord.ui.button(label="Close Ticket", style=discord.ButtonStyle.red)
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not any(role.id in ADMINISTRATOR_ROLE_ID for role in interaction.user.roles):
            await interaction.response.send_message("You do not have permission to close this ticket.", ephemeral=True)
            return

        modal = TicketReasonModal(self.channel, self.member)
        await interaction.response.send_modal(modal)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')

    panel_channel = bot.get_channel(PANEL_CHANNEL_ID)

    if panel_channel:
        embed = discord.Embed(title='NAME', description='description', color=0x34c6eb)
        view = TicketDropdownView()
        await panel_channel.send(embed=embed, view=view)
    else:
        print(f'Channel with ID {PANEL_CHANNEL_ID} not found. Message was not sent')


bot.run('your bot token')
