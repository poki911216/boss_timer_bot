import discord
from discord.ext import commands
from discord.ui import View, Button, Select
import asyncio
from datetime import datetime, timedelta
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(
    command_prefix='!',
    intents=intents,
    reconnect=True  # ⭐ 自動重連
)
@bot.event
async def on_ready():
    print(f"✅ Bot 已上線：{bot.user}")
@bot.event
async def on_command_error(ctx, error):
    print(f"❌ 指令錯誤：{error}")


ROLE_ID = 1450513362545803265  # ← 換成你的提醒身分組 ID

AREAS = [
    "w角", "左愛心房", "中間", "右愛心房",
    "s角", "NE", "塔尖", "2F", "outside"
]

timers = {}
DEFAULT_MINUTES = 45
bot.current_minutes = DEFAULT_MINUTES


def generate_status():
    now = datetime.now()
    text = f"🎮 **Boss 倒數計時面板**\n⏱ 目前倒數時間：**{bot.current_minutes} 分鐘**\n\n"
    for area in AREAS:
        if area in timers:
            remain = int((timers[area]["end"] - now).total_seconds())
            if remain > 0:
                text += f"**{area}** ⏳ 剩餘 {remain//60}分 {remain%60}秒\n"
            else:
                text += f"**{area}** ✅ 已可重生\n"
        else:
            text += f"**{area}** 尚未擊殺\n"
    return text


class TimeSelect(Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="30 分鐘", value="30"),
            discord.SelectOption(label="45 分鐘（預設）", value="45"),
            discord.SelectOption(label="60 分鐘", value="60"),
        ]
        super().__init__(placeholder="⏱ 選擇倒數時間", options=options)

    async def callback(self, interaction: discord.Interaction):
        bot.current_minutes = int(self.values[0])
        await interaction.response.edit_message(
            content=generate_status(), view=self.view
        )


class BossButton(Button):
    def __init__(self, area):
        super().__init__(label=f"🎯 {area}", style=discord.ButtonStyle.success)
        self.area = area

    async def callback(self, interaction: discord.Interaction):
        now = datetime.now()
        end = now + timedelta(minutes=bot.current_minutes)
        timers[self.area] = {"end": end, "channel": interaction.channel}

        await interaction.response.edit_message(
            content=generate_status(), view=self.view
        )

        bot.loop.create_task(countdown(self.area, end, interaction.channel))


async def countdown(area, end, channel):
    await asyncio.sleep((end - datetime.now()).total_seconds())
    role = channel.guild.get_role(ROLE_ID)
    await channel.send(f"🔔 **{area} Boss 已重生！** {role.mention}")


class ControlView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TimeSelect())
        for area in AREAS:
            self.add_item(BossButton(area))


@bot.command()
async def start(ctx):
    await ctx.send(generate_status(), view=ControlView())


@bot.command()
async def reset(ctx):
    timers.clear()
    await ctx.send("♻ **所有 Boss 計時已重置**")

import os

TOKEN = os.getenv("DISCORD_TOKEN")

bot.run(TOKEN)


