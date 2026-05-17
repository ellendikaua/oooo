import discord
from discord.ext import commands
from discord import app_commands
import random
import asyncio

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# -------------------------
# BOT ONLINE
# -------------------------


@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync()

        print(f"✅ {len(synced)} comandos sincronizados")

    except Exception as e:
        print(e)

    print(f"✅ Online como {bot.user}")


# -------------------------
# BOTÃO REROLL
# -------------------------


class RerollView(discord.ui.View):
    def __init__(self, participantes, premio, winners, imagem=None):
        super().__init__(timeout=None)

        self.participantes = participantes
        self.premio = premio
        self.winners = winners
        self.imagem = imagem

    @discord.ui.button(label="Reroll", style=discord.ButtonStyle.primary, emoji="🔄")
    async def reroll(self, interaction: discord.Interaction, button: discord.ui.Button):
        if len(self.participantes) == 0:
            embed = discord.Embed(
                description="❌ Não há participantes.", color=0xED4245
            )

            await interaction.response.send_message(embed=embed, ephemeral=True)

            return

        vencedores = random.sample(
            self.participantes, min(self.winners, len(self.participantes))
        )

        texto = "\n".join([f"🥇 {vencedor.mention}" for vencedor in vencedores])

        embed = discord.Embed(
            title="🔄 NOVO RESULTADO",
            description=f"""
🎁 **{self.premio}**

{texto}
""",
            color=0x5865F2,
        )

        if self.imagem:
            embed.set_image(url=self.imagem)

        await interaction.response.send_message(embed=embed)


# -------------------------
# COMANDO /SORTEIO
# -------------------------


@bot.tree.command(name="sorteio", description="Criar um sorteio profissional")
@app_commands.describe(
    canal="Canal onde o sorteio será enviado",
    horas="Horas do sorteio",
    minutos="Minutos do sorteio",
    premio="Nome do prêmio",
    vencedores="Quantidade de vencedores",
    emoji="Emoji do sorteio",
    cargo="Cargo permitido para participar",
    imagem="Link da imagem/banner",
)
async def sorteio(
    interaction: discord.Interaction,
    canal: discord.TextChannel,
    horas: int,
    minutos: int,
    premio: str,
    vencedores: int,
    emoji: str,
    cargo: discord.Role = None,
    imagem: str = None,
):
    tempo = (horas * 3600) + (minutos * 60)

    class GiveawayView(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=None)

            self.participantes = []

            button = discord.ui.Button(
                label="Participar", style=discord.ButtonStyle.success, emoji=emoji
            )

            button.callback = self.button_callback

            self.add_item(button)

        async def button_callback(self, interaction_button: discord.Interaction):
            usuario = interaction_button.user

            # VERIFICAR CARGO
            if cargo:
                if cargo not in usuario.roles:
                    embed = discord.Embed(
                        description=f"❌ Você precisa do cargo {cargo.mention} para participar.",
                        color=0xED4245,
                    )

                    await interaction_button.response.send_message(
                        embed=embed, ephemeral=True
                    )

                    return

            # VERIFICAR DUPLICADO
            if usuario in self.participantes:
                embed = discord.Embed(
                    description="❌ Você já está participando!", color=0xED4245
                )

                await interaction_button.response.send_message(
                    embed=embed, ephemeral=True
                )

                return

            self.participantes.append(usuario)

            embed = discord.Embed(
                description="✅ Você entrou no sorteio!", color=0x57F287
            )

            await interaction_button.response.send_message(embed=embed, ephemeral=True)

    view = GiveawayView()

    texto_cargo = cargo.mention if cargo else "Todos podem participar"

    embed = discord.Embed(
        title="🎉 NOVO SORTEIO 🎉",
        description=f"""
🎁 **Prêmio:** {premio}

🏆 **Quantidade de vencedores:** {vencedores}

⏰ **Tempo:** {horas}h {minutos}m

🎭 **Cargo permitido:** {texto_cargo}

{emoji} Clique no botão abaixo para participar!
""",
        color=0xC77DFF,
    )

    embed.set_footer(text=f"Criado por {interaction.user}")

    if imagem:
        embed.set_image(url=imagem)

    await canal.send(embed=embed, view=view)

    embed_confirmacao = discord.Embed(
        description=f"✅ Sorteio enviado em {canal.mention}", color=0x57F287
    )

    await interaction.response.send_message(embed=embed_confirmacao, ephemeral=True)

    # ESPERAR TEMPO
    await asyncio.sleep(tempo)

    participantes = view.participantes

    # SEM PARTICIPANTES
    if len(participantes) == 0:
        embed = discord.Embed(
            description="❌ Ninguém participou do sorteio.", color=0xED4245
        )

        await canal.send(embed=embed)

        return

    # ESCOLHER VENCEDORES
    vencedores_lista = random.sample(participantes, min(vencedores, len(participantes)))

    texto_vencedores = "\n".join(
        [f"🥇 {vencedor.mention}" for vencedor in vencedores_lista]
    )

    embed_final = discord.Embed(
        title="🎊 SORTEIO ENCERRADO 🎊",
        description=f"""
🎁 **{premio}**

{texto_vencedores}
""",
        color=0x57F287,
    )

    if imagem:
        embed_final.set_image(url=imagem)

    await canal.send(
        embed=embed_final, view=RerollView(participantes, premio, vencedores, imagem)
    )


# -------------------------
# SISTEMA REACTION ROLE
# -------------------------

reaction_roles = {}


@bot.tree.command(name="reactionrole", description="Criar cargo por reação")
@app_commands.describe(
    canal="Canal da mensagem",
    titulo="Título da mensagem",
    descricao="Descrição da mensagem",
    emoji="Emoji da reação",
    cargo="Cargo que será entregue",
)
async def reactionrole(
    interaction: discord.Interaction,
    canal: discord.TextChannel,
    titulo: str,
    descricao: str,
    emoji: str,
    cargo: discord.Role,
):
    embed = discord.Embed(
        title=titulo,
        description=f"""
{descricao}

Reaja com {emoji} para pegar o cargo {cargo.mention}
""",
        color=0x5865F2,
    )

    mensagem = await canal.send(embed=embed)

    await mensagem.add_reaction(emoji)

    # SALVAR
    reaction_roles[(mensagem.id, emoji)] = cargo.id

    embed_confirm = discord.Embed(
        description="✅ Reaction Role criada com sucesso!", color=0x57F287
    )

    await interaction.response.send_message(embed=embed_confirm, ephemeral=True)


# -------------------------
# GANHAR CARGO
# -------------------------


@bot.event
async def on_raw_reaction_add(payload):
    if payload.user_id == bot.user.id:
        return

    chave = (payload.message_id, str(payload.emoji))

    if chave not in reaction_roles:
        return

    guild = bot.get_guild(payload.guild_id)

    if guild is None:
        return

    membro = guild.get_member(payload.user_id)

    if membro is None:
        return

    cargo_id = reaction_roles[chave]

    cargo = guild.get_role(cargo_id)

    if cargo is None:
        return

    await membro.add_roles(cargo)


# -------------------------
# REMOVER CARGO
# -------------------------


@bot.event
async def on_raw_reaction_remove(payload):
    chave = (payload.message_id, str(payload.emoji))

    if chave not in reaction_roles:
        return

    guild = bot.get_guild(payload.guild_id)

    if guild is None:
        return

    membro = guild.get_member(payload.user_id)

    if membro is None:
        return

    cargo_id = reaction_roles[chave]

    cargo = guild.get_role(cargo_id)

    if cargo is None:
        return

    await membro.remove_roles(cargo)


# -------------------------
# TOKEN
# -------------------------

bot.run("MTM4ODUzODA4MzcxMjE3MjA2Mg.GuEbhX.axvhJWTLM25YF8WyyeD9-vQO21rpFVVx_6-K4s")
