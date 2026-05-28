# ============================================
# Discord Ticket Bot (Python)
# 功能：
# - 建立 Ticket 按鈕
# - 點擊後自動建立私人頻道
# - 管理員可查看
# - 可關閉 Ticket
#
# 安裝：
# pip install -U discord.py
#
# 使用：
# 1. 把 TOKEN 換成你的機器人 Token
# 2. 執行 python bot.py
# 3. Discord 輸入 !setup
# ============================================
import os
import discord
from discord.ext import commands
from discord.ui import View, Button
from flask import Flask
from threading import Thread


TOKEN  = os.getenv("TOKEN")
CHANNEL_ID = "1040861224285515886"

WELCOME_IMAGE_PATH = "image.png"

# ===== Intents =====
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)


app = Flask('')

@app.route('/')
def home():
    return "Bot is alive!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# ============================================
# 關閉 Ticket 按鈕
# ============================================
class CloseTicket(View):

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="關閉私人下單區",
        style=discord.ButtonStyle.danger,
        emoji="🔒"
    )
    async def close(
            self,
            interaction: discord.Interaction,
            button: Button
    ):
        await interaction.response.send_message(
            "Ticket 已關閉",
            ephemeral=True
        )

        await interaction.channel.delete()
    # ============================================


class JumpToChannelView(discord.ui.View):
    def __init__(self, jump_url: str):
        super().__init__(timeout=60)  # 設定 60 秒後按鈕失效 (可依需求調整或設為 None)

        # 動態新增一個超連結按鈕 (Link Button)
        self.add_item(discord.ui.Button(
            label="👉 點我直接跳轉到專屬頻道",
            url=jump_url,
            style=discord.ButtonStyle.link
        ))

# 建立 Ticket 按鈕
# ============================================
class TicketView(View):

    def __init__(self):
        super().__init__(timeout=None)


    @discord.ui.button(
        label="🎫 建立訂單",
        style=discord.ButtonStyle.green
    )
    async def ticket_button(
            self,
            interaction: discord.Interaction,
            button: Button
    ):
        guild = interaction.guild
        user = interaction.user

        # 防止重複開 Ticket
        existing = discord.utils.get(
            guild.channels,
            name=f"ticket-{user.name.lower()}"
        )

        if existing:
            await interaction.response.send_message(
                f"你已經有 Ticket：{existing.mention}",
                ephemeral=True
            )
            return

        # 權限設定
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(
                read_messages=False
            ),

            user: discord.PermissionOverwrite(
                read_messages=True,
                send_messages=True,
                attach_files=True
            ),

            guild.me: discord.PermissionOverwrite(
                read_messages=True,
                send_messages=True
            )
        }

        category_id = 1508478632018968576
        category = guild.get_channel(category_id)

        # 建立頻道
        channel = await guild.create_text_channel(
            name=f"ticket-{user.name}",
            overwrites=overwrites,
            category= category
        )

        embed = discord.Embed(
            title="🎫 您的私人頻道已建立",
            description=f"{user.mention} 歡迎老闆！ 您可以在此頻道敘說您的要求！\n"
                        f"此地只有客服和老闆您可以觀看! \n"
                        f"不用擔心您的隱私被別人打擾!\n"
                        f"客服看到將會盡快回復!\n",
            color=discord.Color.green()
        )

        await channel.send(
            embed=embed,
            view=CloseTicket()
        )
        jump_view = JumpToChannelView(channel.jump_url)

        await interaction.response.send_message(
            f"✅ Ticket 已建立：{channel.mention}",
            ephemeral=True
        )
    # ============================================


# Bot 上線
# ============================================
@bot.event
async def on_ready():
    print(f"✅ 已登入：{bot.user}")
    channel = bot.get_channel(1455465761400295548)

    if channel is not None:
        # 建立上線通知的 Embed
        ready_embed = discord.Embed(
            title="🤖御鋒私人下單區",
            description="點擊下方按鈕創建您私人的下單聯絡頻道！",
            color=0x2ECC71,  # 綠色代表上線狀態
        )

        try:
            await channel.send(embed=ready_embed,view = TicketView())
            print("已成功發送機器人上線通知 Embed！")
        except discord.Forbidden:
            print("提示：機器人沒有權限在頻道中發送上線通知訊息。")
        except Exception as e:
            print(f"發送上線通知 Embed 時發生錯誤: {e}")

# ============================================
# 發送 Ticket 面板
# ============================================
@bot.command()
@commands.has_permissions(administrator=True)
async def setup(ctx):
    embed = discord.Embed(
        title="🤖御鋒私人下單區",
        description="點擊下方按鈕創建您私人的下單聯絡頻道！",
        color=discord.Color.blurple()
    )

    await ctx.send(
        embed=embed,
        view=TicketView()
    )


# =================================================================================================================================================
@bot.event
async def on_member_join(member):
    """
    當有新成員加入伺服器時觸發
    """
    # 取得指定的歡迎頻道
    channel = bot.get_channel(1509162324131446904)

    # 如果找不到該頻道，在後台印出錯誤訊息
    if channel is None:
        print(f"錯誤：請確認 ID 是否正確，且機器人有權限看見該頻道。")
        return

    # 建立歡迎訊息
    # member.mention 會自動產生 @成員 的標記效果
    welcome_message = (
        f"🎉 熱烈歡迎 {member.mention} 加入我們的伺服器！ 🎉\n"
        f"很高興認識你，希望你在這裡玩得開心！如果有任何問題，歡迎詢問管理員喔～"
    )

    embed = discord.Embed(
        title="歡迎來到御鋒電競 𝗬𝗙 𝗖𝗟𝗨𝗕 ",
        description=f"陪玩俱樂部 | 陪玩｜代肝｜代打\n"
                    f"營業時間：𝟴:𝟬𝟬𝗮𝗺 ~ 𝟰:𝟬𝟬𝗮𝗺\n"
                    f"各種需求都可以跟著導航走喔~!\n"
                    f"點單規則<#{1508481484493946982}>\n"
                    f"點單大廳<#{1455465761400295548}>\n"
                    f"考核要求<#{1508494220917473420}>\n"
                    f"應徵打手<#{1508494518679371897}>\n",

        color=discord.Color.orange()
    )
    image_file = None
    if os.path.exists(WELCOME_IMAGE_PATH):
        # 取得檔案名稱（例如 "image2.jpg"）
        filename = os.path.basename(WELCOME_IMAGE_PATH)
        # 建立 discord.File 對象
        image_file = discord.File(WELCOME_IMAGE_PATH, filename=filename)
        # 設定 Embed 的圖片指向該附件
        embed.set_image(url=f"attachment://{filename}")
    else:
        print(f"警告：找不到路徑為 '{WELCOME_IMAGE_PATH}' 的圖片檔案。Embed 將不會顯示圖片。")
    try:
        # 發送訊息到歡迎頻道
        await channel.send(embed=embed,file=image_file)
        print(f"已成功歡迎新成員：{member.name} (ID: {member.id})")
    except discord.Forbidden:
        print(f"錯誤：機器人沒有權限在頻道 {channel.name} 發送訊息。")
    except Exception as e:
        print(f"發送歡迎訊息時發生未知錯誤：{e}")


@bot.command()
@commands.has_permissions(administrator=True)
async def Test(ctx):
    channel = bot.get_channel(1508506343370391632)

    embed = discord.Embed(
        title="我是慈慈",
        description=f"這是一隻豬，請跟我說歡迎。\n"
                    f"<#{1509162324131446904}>",

        color=discord.Color.orange()
    )

    # 我們需要透過 discord.File 將圖片上傳，並用 attachment:// 協議來引用它
    image_file = None
    if os.path.exists(WELCOME_IMAGE_PATH):
        # 取得檔案名稱（例如 "image2.jpg"）
        filename = os.path.basename(WELCOME_IMAGE_PATH)
        # 建立 discord.File 對象
        image_file = discord.File(WELCOME_IMAGE_PATH, filename=filename)
        # 設定 Embed 的圖片指向該附件
        embed.set_image(url=f"attachment://{filename}")
    else:
        print(f"警告：找不到路徑為 '{WELCOME_IMAGE_PATH}' 的圖片檔案。Embed 將不會顯示圖片。")
    try:
        # 發送訊息到歡迎頻道
        await ctx.send(embed=embed,file=image_file)
    except discord.Forbidden:
        print(f"錯誤：機器人沒有權限在頻道 {channel.name} 發送訊息。")
    except Exception as e:
        print(f"發送歡迎訊息時發生未知錯誤：{e}")


# ============================================
# 啟動 Bot
# ============================================
keep_alive()
bot.run(TOKEN)