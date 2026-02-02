           await interaction.response.send_message(f"❌ Error: {e}", ephemeral=True)

# --- 🎭 [View] ระบบ Self-Role (รับยศอัตโนมัติ) ---
class PersistentRoleView(discord.ui.View):
    def __init__(self, bot_instance):
        super().__init__(timeout=None)
        self.bot = bot_instance

    @discord.ui.button(label="รับ/คืนยศ", style=discord.ButtonStyle.primary, custom_id="role_ultimate_btn")
    async def role_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        data = self.bot.load_data(interaction.guild.id, "self_role")
        role = interaction.guild.get_role(data.get('role_id'))
        if not role: return await interaction.response.send_message("❌ ไม่พบยศในระบบ", ephemeral=True)
        
        if role in interaction.user.roles:
            await interaction.user.remove_roles(role)
            await interaction.response.send_message(f"❌ คืนยศ **{role.name}** เรียบร้อยแล้ว", ephemeral=True)
        else:
            try:
                await interaction.user.add_roles(role)
                await interaction.response.send_message(f"✅ รับยศ **{role.name}** เรียบร้อยแล้ว", ephemeral=True)
            except:
                await interaction.response.send_message("❌ บอทไม่มีอำนาจให้ยศ (โปรดเช็คว่ายศบอทอยู่สูงกว่ายศที่แจก)", ephemeral=True)

# ==========================================
#      🛡️ [ระบบความปลอดภัยครบชุด - Version: Auto Penalty]
# ==========================================

# --- 1. ตัวเลือกคำสั่ง ---
PENALTY_CHOICES = [
    app_commands.Choice(name="ระงับการโต้ตอบ (Timeout)", value="timeout"),
    app_commands.Choice(name="แบน (Ban)", value="ban")
]

# ตัวเลือกเวลา Timeout ตามที่พี่ต้องการ
TIMEOUT_CHOICES = [
    app_commands.Choice(name="1 นาที", value=1),
    app_commands.Choice(name="5 นาที", value=5),
    app_commands.Choice(name="10 นาที", value=10),
    app_commands.Choice(name="1 ชั่วโมง", value=60),
    app_commands.Choice(name="1 วัน", value=1440),
    app_commands.Choice(name="7 วัน", value=10080),
]

DISABLE_CHOICES = [
    app_commands.Choice(name="ปิดกันลิงก์", value="security_link"),
    app_commands.Choice(name="ปิดกันโปรโมท", value="security_promo"),
    app_commands.Choice(name="ปิดกันสแปม", value="security_spam"),
    app_commands.Choice(name="ปิดทั้งหมด", value="all")
]

# --- 2. ฟังก์ชันลงโทษหลัก (ประมวลผลทันที) ---
async def process_security_violation(message, data, reason):
    member = message.author
    penalty = data.get('penalty')
    log_chan = message.guild.get_channel(data.get('log_id'))
    t_mins = data.get('timeout_mins', 5)
    
    try: await message.delete()
    except: pass

    if penalty == "ban":
        try:
            await member.send(f"⚠️ คุณถูกแบนจาก {message.guild.name}\nสาเหตุ: {reason}")
            await member.ban(reason=reason)
            if log_chan:
                embed = discord.Embed(title="🔨 [BAN] ลงโทษเด็ดขาด", color=0xff0000)
                embed.description = f"**ผู้กระทำผิด:** {member.mention}\n**สาเหตุ:** {reason}\n**ห้อง:** {message.channel.mention}"
                await log_chan.send(embed=embed)
        except: pass
    
    elif penalty == "timeout":
        try:
            duration = datetime.timedelta(minutes=int(t_mins))
            await member.timeout(duration, reason=reason)
            
            # ส่ง DM บอกคนโดน
            try: await member.send(f"⚠️ คุณถูกระงับโต้ตอบใน {message.guild.name} เป็นเวลา {t_mins} นาที\nสาเหตุ: {reason}")
            except: pass

            if log_chan:
                embed = discord.Embed(title="⏱️ [TIMEOUT] ลงโทษอัตโนมัติ", color=0xffa500)
                embed.description = (
                    f"**ผู้กระทำผิด:** {member.mention}\n"
                    f"**เวลาที่ลงโทษ:** {t_mins} นาที\n"
                    f"**สาเหตุ:** {reason}\n"
                    f"**ห้อง:** {message.channel.mention}"
                )
                await log_chan.send(embed=embed)
        except Exception as e:
            if log_chan: await log_chan.send(f"❌ ลงโทษ {member.mention} ไม่ได้: {e}")

# --- 3. คำสั่งตั้งค่า (ลิงก์/โปรโมท/สแปม) ---
@bot.tree.command(name="anti_link", description="เปิดระบบกันลิงก์ (เลือกเวลาได้)")
@app_commands.choices(penalty=PENALTY_CHOICES, timeout_mins=TIMEOUT_CHOICES)
async def anti_link(interaction: discord.Interaction, penalty: str, log_channel: discord.TextChannel, timeout_mins: int = 5):
    if not bot.check_admin(interaction): return
    bot.save_data(interaction.guild.id, "security_link", {"penalty": penalty, "log_id": log_channel.id, "timeout_mins": timeout_mins})
    await interaction.response.send_message(f"✅ ตั้งกันลิงก์เรียบร้อย (Penalty: {penalty} | Time: {timeout_mins}m)", ephemeral=True)

@bot.tree.command(name="anti_promo", description="เปิดระบบกันโปรโมท (เลือกเวลาได้)")
@app_commands.choices(penalty=PENALTY_CHOICES, timeout_mins=TIMEOUT_CHOICES)
async def anti_promo(interaction: discord.Interaction, penalty: str, log_channel: discord.TextChannel, timeout_mins: int = 5):
    if not bot.check_admin(interaction): return
    bot.save_data(interaction.guild.id, "security_promo", {"penalty": penalty, "log_id": log_channel.id, "timeout_mins": timeout_mins})
    await interaction.response.send_message(f"✅ ตั้งกันโปรโมทเรียบร้อย (Penalty: {penalty} | Time: {timeout_mins}m)", ephemeral=True)

@bot.tree.command(name="anti_spam", description="เปิดระบบกันสแปม (เลือกเวลาได้)")
@app_commands.choices(penalty=PENALTY_CHOICES, timeout_mins=TIMEOUT_CHOICES)
async def anti_spam(interaction: discord.Interaction, penalty: str, log_channel: discord.TextChannel, timeout_mins: int = 5):
    if not bot.check_admin(interaction): return
    bot.save_data(interaction.guild.id, "security_spam", {"penalty": penalty, "log_id": log_channel.id, "timeout_mins": timeout_mins})
    await interaction.response.send_message(f"✅ ตั้งกันสแปมเรียบร้อย (Penalty: {penalty} | Time: {timeout_mins}m)", ephemeral=True)

@bot.tree.command(name="anti_off", description="เลือกปิดระบบการป้องกัน")
@app_commands.choices(target=DISABLE_CHOICES)
async def setup_disable(interaction: discord.Interaction, target: str):
    if not bot.check_admin(interaction): return
    if target == "all":
        for key in ["security_link", "security_promo", "security_spam"]: bot.save_data(interaction.guild.id, key, {})
        msg = "🚫 ปิดระบบการป้องกันทั้งหมดแล้ว"
    else:
        bot.save_data(interaction.guild.id, target, {})
        msg = f"✅ ปิดระบบการป้องกันที่เลือกเรียบร้อย"
    await interaction.response.send_message(msg, ephemeral=True)
# --- 5. [ ⚪ WHITELIST SYSTEM - UPGRADED ] ---
@bot.tree.command(name="whitelist_add", description="เพิ่มคน, ช่อง หรือหมวดหมู่ที่ยกเว้นการตรวจสอบ")
@app_commands.describe(
    target_member="สมาชิกที่ต้องการยกเว้น",
    target_channel="ห้องแชทที่ต้องการยกเว้น",
    target_category="หมวดหมู่ที่ต้องการยกเว้น (ทั้งหมวด)"
)
async def whitelist_add(
    interaction: discord.Interaction, 
    target_member: discord.Member = None, 
    target_channel: discord.TextChannel = None,
    target_category: discord.CategoryChannel = None
):
    if not bot.check_admin(interaction): return
    
    # โหลดข้อมูล (เพิ่มโครงสร้าง categories)
    data = bot.load_data(interaction.guild.id, "whitelist") or {"channels": [], "members": [], "categories": []}
    if "categories" not in data: data["categories"] = []

    msg_parts = []
    if target_member: 
        if target_member.id not in data["members"]:
            data["members"].append(target_member.id)
            msg_parts.append(f"สมาชิก: {target_member.mention}")
            
    if target_channel: 
        if target_channel.id not in data["channels"]:
            data["channels"].append(target_channel.id)
            msg_parts.append(f"ห้องแชท: {target_channel.mention}")

    if target_category:
        if target_category.id not in data["categories"]:
            data["categories"].append(target_category.id)
            msg_parts.append(f"หมวดหมู่: **{target_category.name}**")

    if not msg_parts:
        return await interaction.response.send_message("❌ กรุณาเลือกอย่างน้อยหนึ่งอย่าง (สมาชิก/ห้อง/หมวดหมู่)", ephemeral=True)

    bot.save_data(interaction.guild.id, "whitelist", data)
    await interaction.response.send_message(f"✅ เพิ่มเข้าไวท์ลิสต์แล้ว: {', '.join(msg_parts)}", ephemeral=True)

@bot.tree.command(name="whitelist_remove", description="ลบออกจากไวท์ลิสต์")
async def whitelist_remove(
    interaction: discord.Interaction, 
    target_member: discord.Member = None, 
    target_channel: discord.TextChannel = None,
    target_category: discord.CategoryChannel = None
):
    if not bot.check_admin(interaction): return
    data = bot.load_data(interaction.guild.id, "whitelist") or {"channels": [], "members": [], "categories": []}
    
    if target_member and target_member.id in data.get("members", []): data["members"].remove(target_member.id)
    if target_channel and target_channel.id in data.get("channels", []): data["channels"].remove(target_channel.id)
    if target_category and target_category.id in data.get("categories", []): data["categories"].remove(target_category.id)
    
    bot.save_data(interaction.guild.id, "whitelist", data)
    await interaction.response.send_message("🗑️ ลบข้อมูลที่เลือกออกจากไวท์ลิสต์แล้ว", ephemeral=True)

@bot.tree.command(name="whitelist_list", description="ดูรายชื่อไวท์ลิสต์ทั้งหมด")
async def whitelist_list(interaction: discord.Interaction):
    if not bot.check_admin(interaction): return
    data = bot.load_data(interaction.guild.id, "whitelist") or {"channels": [], "members": [], "categories": []}
    
    embed = discord.Embed(title="🏳️ รายการ Whitelist (ข้อยกเว้น)", color=0xffffff)
    
    m_list = [f"• <@{m}>" for m in data.get("members", [])]
    c_list = [f"• <#{c}>" for c in data.get("channels", [])]
    cat_list = [f"• 📂 **{interaction.guild.get_channel(cat).name if interaction.guild.get_channel(cat) else cat}**" for cat in data.get("categories", [])]
    
    embed.add_field(name="👥 สมาชิก", value="\n".join(m_list) or "ไม่มี", inline=Trueimport discord
from discord import app_commands
from discord.ext import commands
import os
from dotenv import load_dotenv
import json
import datetime
import re
import asyncio

# ==========================================
#      [ CONFIGURATION ]
# ==========================================
load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID"))
# ==========================================

class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.all()
        super().__init__(command_prefix="!", intents=intents)
        self.spam_control = {}

    # --- 📁 ระบบจัดการฐานข้อมูลไฟล์ .txt ---
    def save_data(self, guild_id, filename, data):
        path = f"database/{guild_id}"
        if not os.path.exists(path): os.makedirs(path)
        with open(f"{path}/{filename}.txt", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    def load_data(self, guild_id, filename):
        path = f"database/{guild_id}/{filename}.txt"
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f: return json.load(f)
        return {}

    def check_admin(self, target):
        user = target.user if hasattr(target, 'user') else target.author
        if user.id == OWNER_ID: return True
        if hasattr(user, 'guild_permissions') and user.guild_permissions.administrator: return True
        data = self.load_data(target.guild.id, "admins") or {"users": [], "roles": []}
        if user.id in data.get("users", []): return True
        if hasattr(user, 'roles') and any(r.id in data.get("roles", []) for r in user.roles): return True
        return False

    async def setup_hook(self):
        # ทำให้ปุ่มกดทำงานได้ตลอดเวลาแม้รีสตาร์ทบอท
        self.add_view(PersistentTicketView(self))
        self.add_view(PersistentRoleView(self))
        await self.tree.sync()
        print(f"🚀 บอท {self.user} พร้อมทำงานแบบเต็มสูบแล้ว!")

bot = MyBot()

# --- 🎫 [View] ระบบ Ticket (ฉบับบล็อกเจ้าของบอทถาวร) ---
class PersistentTicketView(discord.ui.View):
    def __init__(self, bot_instance):
        super().__init__(timeout=None)
        self.bot = bot_instance

    @discord.ui.button(label="เปิดทิกเก็ต / ขอความช่วยเหลือ", style=discord.ButtonStyle.success, custom_id="tk_ultimate_btn")
    async def ticket_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        data = self.bot.load_data(interaction.guild.id, "ticket")
        if not data: 
            return await interaction.response.send_message("❌ ระบบยังไม่ได้ตั้งค่า", ephemeral=True)
        
        category = interaction.guild.get_channel(data.get('category_id'))
        admin_role = interaction.guild.get_role(data.get('admin_role_id'))
        
        # --- กำหนดสิทธิ์แบบล็อคตายตัว ---
        overwrites = {
            # 1. ปิดทุกคน (@everyone)
            interaction.guild.default_role: discord.PermissionOverwrite(view_channel=False),
            
            # 2. ให้คนเปิดเห็นและคุยได้
            interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True, attach_files=True),
            
            # 3. ให้ตัวบอทเห็น (เพื่อทำงาน)
            interaction.guild.me: discord.PermissionOverwrite(view_channel=True, manage_channels=True)
        }

        # 4. 🔥 [จุดสำคัญ] สั่งปิดการมองเห็นของ "เจ้าของบอท" โดยเฉพาะ
        # บรรทัดนี้จะไป override สิทธิ์อื่นๆ ทำให้เจ้าของบอทมองไม่เห็นช่องนี้
        owner = interaction.guild.get_member(self.bot.owner_id) # ดึงตัวพี่เอง
        if owner:
            overwrites[owner] = discord.PermissionOverwrite(view_channel=False)

        # 5. ให้ยศแอดมินของเซิร์ฟเวอร์นั้นๆ เห็นได้
        if admin_role: 
            overwrites[admin_role] = discord.PermissionOverwrite(view_channel=True, send_messages=True)
        
        # สร้างช่อง
        try:
            channel = await interaction.guild.create_text_channel(
                name=f"ช่วยเหลือ-{interaction.user.name}", 
                category=category, 
                overwrites=overwrites
            )
            await interaction.response.send_message(f"✅ สร้างช่องช่วยเหลือของคุณแล้ว: {channel.mention}", ephemeral=True)
            
            embed = discord.Embed(title="🎫 ระบบช่วยเหลือ", description=f"สวัสดีคุณ {interaction.user.mention}\nทีมงานแอดมินจะรีบมาตรวจสอบครับ", color=0x2ecc71)
            await channel.send(embed=embed)
        except Exception as e:
            await interaction.response.send_message(f"❌ Error: {e}", ephemeral=True)

# --- 🎭 [View] ระบบ Self-Role (รับยศอัตโนมัติ) ---
class PersistentRoleView(discord.ui.View):
    def __init__(self, bot_instance):
        super().__init__(timeout=None)
        self.bot = bot_instance

    @discord.ui.button(label="รับ/คืนยศ", style=discord.ButtonStyle.primary, custom_id="role_ultimate_btn")
    async def role_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        data = self.bot.load_data(interaction.guild.id, "self_role")
        role = interaction.guild.get_role(data.get('role_id'))
        if not role: return await interaction.response.send_message("❌ ไม่พบยศในระบบ", ephemeral=True)
        
        if role in interaction.user.roles:
            await interaction.user.remove_roles(role)
            await interaction.response.send_message(f"❌ คืนยศ **{role.name}** เรียบร้อยแล้ว", ephemeral=True)
        else:
            try:
                await interaction.user.add_roles(role)
                await interaction.response.send_message(f"✅ รับยศ **{role.name}** เรียบร้อยแล้ว", ephemeral=True)
            except:
                await interaction.response.send_message("❌ บอทไม่มีอำนาจให้ยศ (โปรดเช็คว่ายศบอทอยู่สูงกว่ายศที่แจก)", ephemeral=True)

# ==========================================
#      🛡️ [ระบบความปลอดภัยครบชุด - Version: Auto Penalty]
# ==========================================

# --- 1. ตัวเลือกคำสั่ง ---
PENALTY_CHOICES = [
    app_commands.Choice(name="ระงับการโต้ตอบ (Timeout)", value="timeout"),
    app_commands.Choice(name="แบน (Ban)", value="ban")
]

# ตัวเลือกเวลา Timeout ตามที่พี่ต้องการ
TIMEOUT_CHOICES = [
    app_commands.Choice(name="1 นาที", value=1),
    app_commands.Choice(name="5 นาที", value=5),
    app_commands.Choice(name="10 นาที", value=10),
    app_commands.Choice(name="1 ชั่วโมง", value=60),
    app_commands.Choice(name="1 วัน", value=1440),
    app_commands.Choice(name="7 วัน", value=10080),
]

DISABLE_CHOICES = [
    app_commands.Choice(name="ปิดกันลิงก์", value="security_link"),
    app_commands.Choice(name="ปิดกันโปรโมท", value="security_promo"),
    app_commands.Choice(name="ปิดกันสแปม", value="security_spam"),
    app_commands.Choice(name="ปิดทั้งหมด", value="all")
]

# --- 2. ฟังก์ชันลงโทษหลัก (ประมวลผลทันที) ---
async def process_security_violation(message, data, reason):
    member = message.author
    penalty = data.get('penalty')
    log_chan = message.guild.get_channel(data.get('log_id'))
    t_mins = data.get('timeout_mins', 5)
    
    try: await message.delete()
    except: pass

    if penalty == "ban":
        try:
            await member.send(f"⚠️ คุณถูกแบนจาก {message.guild.name}\nสาเหตุ: {reason}")
            await member.ban(reason=reason)
            if log_chan:
                embed = discord.Embed(title="🔨 [BAN] ลงโทษเด็ดขาด", color=0xff0000)
                embed.description = f"**ผู้กระทำผิด:** {member.mention}\n**สาเหตุ:** {reason}\n**ห้อง:** {message.channel.mention}"
                await log_chan.send(embed=embed)
        except: pass
    
    elif penalty == "timeout":
        try:
            duration = datetime.timedelta(minutes=int(t_mins))
            await member.timeout(duration, reason=reason)
            
            # ส่ง DM บอกคนโดน
            try: await member.send(f"⚠️ คุณถูกระงับโต้ตอบใน {message.guild.name} เป็นเวลา {t_mins} นาที\nสาเหตุ: {reason}")
            except: pass

            if log_chan:
                embed = discord.Embed(title="⏱️ [TIMEOUT] ลงโทษอัตโนมัติ", color=0xffa500)
                embed.description = (
                    f"**ผู้กระทำผิด:** {member.mention}\n"
                    f"**เวลาที่ลงโทษ:** {t_mins} นาที\n"
                    f"**สาเหตุ:** {reason}\n"
                    f"**ห้อง:** {message.channel.mention}"
                )
                await log_chan.send(embed=embed)
        except Exception as e:
            if log_chan: await log_chan.send(f"❌ ลงโทษ {member.mention} ไม่ได้: {e}")

# --- 3. คำสั่งตั้งค่า (ลิงก์/โปรโมท/สแปม) ---
@bot.tree.command(name="anti_link", description="เปิดระบบกันลิงก์ (เลือกเวลาได้)")
@app_commands.choices(penalty=PENALTY_CHOICES, timeout_mins=TIMEOUT_CHOICES)
async def anti_link(interaction: discord.Interaction, penalty: str, log_channel: discord.TextChannel, timeout_mins: int = 5):
    if not bot.check_admin(interaction): return
    bot.save_data(interaction.guild.id, "security_link", {"penalty": penalty, "log_id": log_channel.id, "timeout_mins": timeout_mins})
    await interaction.response.send_message(f"✅ ตั้งกันลิงก์เรียบร้อย (Penalty: {penalty} | Time: {timeout_mins}m)", ephemeral=True)

@bot.tree.command(name="anti_promo", description="เปิดระบบกันโปรโมท (เลือกเวลาได้)")
@app_commands.choices(penalty=PENALTY_CHOICES, timeout_mins=TIMEOUT_CHOICES)
async def anti_promo(interaction: discord.Interaction, penalty: str, log_channel: discord.TextChannel, timeout_mins: int = 5):
    if not bot.check_admin(interaction): return
    bot.save_data(interaction.guild.id, "security_promo", {"penalty": penalty, "log_id": log_channel.id, "timeout_mins": timeout_mins})
    await interaction.response.send_message(f"✅ ตั้งกันโปรโมทเรียบร้อย (Penalty: {penalty} | Time: {timeout_mins}m)", ephemeral=True)

@bot.tree.command(name="anti_spam", description="เปิดระบบกันสแปม (เลือกเวลาได้)")
@app_commands.choices(penalty=PENALTY_CHOICES, timeout_mins=TIMEOUT_CHOICES)
async def anti_spam(interaction: discord.Interaction, penalty: str, log_channel: discord.TextChannel, timeout_mins: int = 5):
    if not bot.check_admin(interaction): return
    bot.save_data(interaction.guild.id, "security_spam", {"penalty": penalty, "log_id": log_channel.id, "timeout_mins": timeout_mins})
    await interaction.response.send_message(f"✅ ตั้งกันสแปมเรียบร้อย (Penalty: {penalty} | Time: {timeout_mins}m)", ephemeral=True)

@bot.tree.command(name="anti_off", description="เลือกปิดระบบการป้องกัน")
@app_commands.choices(target=DISABLE_CHOICES)
async def setup_disable(interaction: discord.Interaction, target: str):
    if not bot.check_admin(interaction): return
    if target == "all":
        for key in ["security_link", "security_promo", "security_spam"]: bot.save_data(interaction.guild.id, key, {})
        msg = "🚫 ปิดระบบการป้องกันทั้งหมดแล้ว"
    else:
        bot.save_data(interaction.guild.id, target, {})
        msg = f"✅ ปิดระบบการป้องกันที่เลือกเรียบร้อย"
    await interaction.response.send_message(msg, ephemeral=True)
# --- 5. [ ⚪ WHITELIST SYSTEM - UPGRADED ] ---
@bot.tree.command(name="whitelist_add", description="เพิ่มคน, ช่อง หรือหมวดหมู่ที่ยกเว้นการตรวจสอบ")
@app_commands.describe(
    target_member="สมาชิกที่ต้องการยกเว้น",
    target_channel="ห้องแชทที่ต้องการยกเว้น",
    target_category="หมวดหมู่ที่ต้องการยกเว้น (ทั้งหมวด)"
)
async def whitelist_add(
    interaction: discord.Interaction, 
    target_member: discord.Member = None, 
    target_channel: discord.TextChannel = None,
    target_category: discord.CategoryChannel = None
):
    if not bot.check_admin(interaction): return
    
    # โหลดข้อมูล (เพิ่มโครงสร้าง categories)
    data = bot.load_data(interaction.guild.id, "whitelist") or {"channels": [], "members": [], "categories": []}
    if "categories" not in data: data["categories"] = []

    msg_parts = []
    if target_member: 
        if target_member.id not in data["members"]:
            data["members"].append(target_member.id)
            msg_parts.append(f"สมาชิก: {target_member.mention}")
            
    if target_channel: 
        if target_channel.id not in data["channels"]:
            data["channels"].append(target_channel.id)
            msg_parts.append(f"ห้องแชท: {target_channel.mention}")

    if target_category:
        if target_category.id not in data["categories"]:
            data["categories"].append(target_category.id)
            msg_parts.append(f"หมวดหมู่: **{target_category.name}**")

    if not msg_parts:
        return await interaction.response.send_message("❌ กรุณาเลือกอย่างน้อยหนึ่งอย่าง (สมาชิก/ห้อง/หมวดหมู่)", ephemeral=True)

    bot.save_data(interaction.guild.id, "whitelist", data)
    await interaction.response.send_message(f"✅ เพิ่มเข้าไวท์ลิสต์แล้ว: {', '.join(msg_parts)}", ephemeral=True)

@bot.tree.command(name="whitelist_remove", description="ลบออกจากไวท์ลิสต์")
async def whitelist_remove(
    interaction: discord.Interaction, 
    target_member: discord.Member = None, 
    target_channel: discord.TextChannel = None,
    target_category: discord.CategoryChannel = None
):
    if not bot.check_admin(interaction): return
    data = bot.load_data(interaction.guild.id, "whitelist") or {"channels": [], "members": [], "categories": []}
    
    if target_member and target_member.id in data.get("members", []): data["members"].remove(target_member.id)
    if target_channel and target_channel.id in data.get("channels", []): data["channels"].remove(target_channel.id)
    if target_category and target_category.id in data.get("categories", []): data["categories"].remove(target_category.id)
    
    bot.save_data(interaction.guild.id, "whitelist", data)
    await interaction.response.send_message("🗑️ ลบข้อมูลที่เลือกออกจากไวท์ลิสต์แล้ว", ephemeral=True)

@bot.tree.command(name="whitelist_list", description="ดูรายชื่อไวท์ลิสต์ทั้งหมด")
async def whitelist_list(interaction: discord.Interaction):
    if not bot.check_admin(interaction): return
    data = bot.load_data(interaction.guild.id, "whitelist") or {"channels": [], "members": [], "categories": []}
    
    embed = discord.Embed(title="🏳️ รายการ Whitelist (ข้อยกเว้น)", color=0xffffff)
    
    m_list = [f"• <@{m}>" for m in data.get("members", [])]
    c_list = [f"• <#{c}>" for c in data.get("channels", [])]
    cat_list = [f"• 📂 **{interaction.guild.get_channel(cat).name if interaction.guild.get_channel(cat) else cat}**" for cat in data.get("categories", [])]
    
    embed.add_field(name="👥 สมาชิก", value="\n".join(m_list) or "ไม่มี", inline=True)
      embed.add_field(name="📺 ช่องแชท", value="\n".join(c_list) or "ไม่มี", inline=True)
    embed.add_field(name="📁 หมวดหมู่", value="\n".join(cat_list) or "ไม่มี", inline=False)
    
    await interaction.response.send_message(embed=embed, ephemeral=True)

# --- 👋 [ระบบต้อนรับ & คำสั่งทดสอบ] ---

@bot.tree.command(name="set_welcome", description="ตั้งค่าข้อความต้อนรับสมาชิกใหม่")
@app_commands.describe(channel="เลือกห้องที่จะส่งข้อความ", message="พิมพ์ข้อความ (ใช้ {user} แทนชื่อ, {guild} แทนชื่อเซิร์ฟ, {count} แทนจำนวนคน)")
async def set_welcome(interaction: discord.Interaction, channel: discord.TextChannel, message: str):
    if not bot.check_admin(interaction): return
    
    bot.save_data(interaction.guild.id, "welcome", {
        "channel_id": channel.id,
        "message": message
    })
    await interaction.response.send_message(f"✅ ตั้งค่าระบบต้อนรับเรียบร้อยที่ห้อง {channel.mention}", ephemeral=True)

@bot.tree.command(name="test_welcome", description="🧪 ทดสอบส่งข้อความต้อนรับ (ดูตัวอย่าง)")
async def test_welcome(interaction: discord.Interaction):
    if not bot.check_admin(interaction): return
    
    data = bot.load_data(interaction.guild.id, "welcome")
    if not data:
        return await interaction.response.send_message("❌ ยังไม่ได้ตั้งค่าระบบต้อนรับ! กรุณาใช้ `/set_welcome` ก่อน", ephemeral=True)
    
    channel = interaction.guild.get_channel(data['channel_id'])
    if not channel:
        return await interaction.response.send_message("❌ ไม่พบห้องที่ตั้งค่าไว้ (ห้องอาจถูกลบ)", ephemeral=True)
    
    # ดึงข้อความมาแปลง Tags (จำลองว่าตัวพี่เองคือคนเข้าใหม่)
    welcome_msg = data['message'].replace("{user}", interaction.user.mention)\
                                 .replace("{guild}", interaction.guild.name)\
                                 .replace("{count}", str(interaction.guild.member_count))
    
    await channel.send(f"🧪 **[ตัวอย่างข้อความต้อนรับ]**\n{welcome_msg}")
    await interaction.response.send_message(f"✅ ส่งตัวอย่างไปที่ห้อง {channel.mention} เรียบร้อยแล้ว", ephemeral=True)

# ฟังก์ชันทำงานจริงเมื่อมีคนเข้าเซิร์ฟเวอร์
@bot.event
async def on_member_join(member):
    # --- 1. เช็ค Anti-Alt (กันไอดีใหม่) ก่อนตามที่ตั้งไว้ ---
    days_limit = bot.load_data(member.guild.id, "anti_alt_days") or 0
    if days_limit > 0:
        now = datetime.datetime.now(datetime.timezone.utc)
        account_age = (now - member.created_at).days
        if account_age < days_limit:
            try:
                await member.send(f"⚠️ ไอดีคุณอายุไม่ถึง {days_limit} วัน จึงไม่สามารถเข้าเซิร์ฟได้")
                await member.kick(reason="Anti-Alt")
                return # โดนเตะแล้ว ไม่ต้องส่งข้อความต้อนรับด้านล่าง
            except: pass

    # --- 2. ส่งข้อความต้อนรับ (ถ้าผ่าน Anti-Alt มาได้) ---
    data = bot.load_data(member.guild.id, "welcome")
    if data:
        channel = member.guild.get_channel(data['channel_id'])
        if channel:
            # แปลง Tags เป็นข้อมูลจริง
            msg = data['message'].replace("{user}", member.mention)\
                                 .replace("{guild}", member.guild.name)\
                                 .replace("{count}", str(member.guild.member_count))
            await channel.send(msg)

# --- ⚙️ [3] Services Section (Ticket & Role) ---

# --- 🎫 [1] ปุ่มปิดห้องทิกเก็ต (ถาวร) ---
class TicketCloseView(discord.ui.View):
    def __init__(self, bot_instance):
        super().__init__(timeout=None) # ✅ ปุ่มอมตะ
        self.bot = bot_instance

    @discord.ui.button(label="🔒 ปิด Tickets", style=discord.ButtonStyle.danger, custom_id="tk_close_btn_fixed")
    async def close_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.bot.check_admin(interaction):
            return await interaction.response.send_message("❌ เฉพาะแอดมินเท่านั้นที่มีสิทธิ์ลบห้องนี้!", ephemeral=True)
        
        await interaction.response.send_message("⚠️ ห้องนี้จะถูกลบภายใน 3 วินาที...")
        await asyncio.sleep(3)
        await interaction.channel.delete()

# --- 🎫 [2] ปุ่มเปิดทิกเก็ต (ถาวร) ---
class PersistentTicketView(discord.ui.View):
    def __init__(self, bot_instance):
        super().__init__(timeout=None) # ✅ ปุ่มอมตะ
        self.bot = bot_instance

    @discord.ui.button(label="เปิดทิกเก็ต / ขอความช่วยเหลือ", style=discord.ButtonStyle.success, custom_id="tk_ultimate_btn")
    async def ticket_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        data = self.bot.load_data(interaction.guild.id, "ticket")
        if not data: 
            return await interaction.response.send_message("❌ ระบบยังไม่ได้ตั้งค่า กรุณาใช้คำสั่ง /ticket_setup", ephemeral=True)
        
        category = interaction.guild.get_channel(data['category_id'])
        admin_role = interaction.guild.get_role(data['admin_role_id'])
        custom_desc = data.get('description', "กรุณาแจ้งรายละเอียดไว้ที่นี่เพื่อให้ทีมงานตรวจสอบครับ")

        ticket_channel_name = f"ช่วยเหลือ-{interaction.user.name}".lower().replace(" ", "-")
        existing_ticket = discord.utils.get(category.text_channels, name=ticket_channel_name)
        
        if existing_ticket:
            return await interaction.response.send_message(f"❌ คุณมีห้องทิกเก็ตที่เปิดไว้อยู่แล้ว: {existing_ticket.mention}", ephemeral=True)

        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True, attach_files=True),
            interaction.guild.me: discord.PermissionOverwrite(view_channel=True, manage_channels=True)
        }
        if admin_role: overwrites[admin_role] = discord.PermissionOverwrite(view_channel=True)
        
        channel = await interaction.guild.create_text_channel(name=ticket_channel_name, category=category, overwrites=overwrites)
        await interaction.response.send_message(f"✅ สร้างช่องช่วยเหลือแล้ว: {channel.mention}", ephemeral=True)
        
        await channel.send(interaction.user.mention)
        embed = discord.Embed(title="🎫 ห้อง Ticket", description=custom_desc, color=0x2ecc71)
        await channel.send(embed=embed, view=TicketCloseView(self.bot)) # ✅ ส่งปุ่มปิดถาวรไปด้วย

# --- 🎫 [3] คำสั่งจัดการ Ticket ---
@bot.tree.command(name="ticket_setup", description="ตั้งค่าระบบทิกเก็ต")
async def ticket_setup(interaction: discord.Interaction, category: discord.CategoryChannel, admin_role: discord.Role, title: str, description: str, button_text: str = "เปิดทิกเก็ต", emoji: str = "🎫"):
    if not bot.check_admin(interaction): return
    bot.save_data(interaction.guild.id, "ticket", {"category_id": category.id, "admin_role_id": admin_role.id, "title": title, "description": description, "button_text": button_text, "emoji": emoji})
    await interaction.response.send_message("✅ ตั้งค่าเรียบร้อย! ใช้ `/ticket_send` เพื่อส่งปุ่ม", ephemeral=True)

@bot.tree.command(name="ticket_send", description="ส่งระบบทิกเก็ตไปยังช่องที่เลือก")
async def ticket_send(interaction: discord.Interaction, channel: discord.TextChannel):
    if not bot.check_admin(interaction): return
    data = bot.load_data(interaction.guild.id, "ticket")
    if not data: return await interaction.response.send_message("❌ ยังไม่ได้ตั้งค่า", ephemeral=True)
    view = PersistentTicketView(bot)
    view.children[0].label, view.children[0].emoji = data.get("button_text"), data.get("emoji")
    embed = discord.Embed(title=data.get("title"), description=data.get("description"), color=0x3498db)
    await channel.send(embed=embed, view=view)
    await interaction.response.send_message(f"✅ ส่งไปที่ {channel.mention} แล้ว", ephemeral=True)


@bot.tree.command(name="role_setup", description="ติดตั้งปุ่มรับยศ (ใส่รูปได้)")
async def role_setup(interaction: discord.Interaction, role: discord.Role, title: str, description: str, button_text: str, emoji: str, image_url: str = None):
    if not bot.check_admin(interaction): return
    bot.save_data(interaction.guild.id, "self_role", {"role_id": role.id})
    view = PersistentRoleView(bot)
    view.children[0].label = button_text
    view.children[0].emoji = emoji
    embed = discord.Embed(title=title, description=description, color=0x9b59b6)
    if image_url:
        embed.set_image(url=image_url)
    await interaction.channel.send(embed=embed, view=view)
    await interaction.response.send_message("✅ ติดตั้งระบบปุ่มรับยศเรียบร้อย!", ephemeral=True)

# --- 🖋️ [Fancy Text System] ---

@bot.tree.command(name="fancy_text", description="แปลงข้อความเป็นตัวอักษรพิเศษ (Small Caps)")
@app_commands.describe(text="พิมพ์ข้อความภาษาอังกฤษที่ต้องการแปลง")
async def fancy_text(interaction: discord.Interaction, text: str):
    # ตารางเทียบตัวอักษรปกติ กับ ตัวอักษรพิเศษที่พี่ให้มา
    normal_chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
    fancy_chars  = "ᴀʙᴄᴅᴇꜰɢʜɪᴊᴋʟᴍɴᴏᴘQʀꜱᴛᴜᴠᴡxʏᴢᴀʙᴄᴅᴇꜰɢʜɪᴊᴋʟᴍɴᴏᴘQʀꜱᴛᴜᴠᴡxʏᴢ"
    
    # สร้างตารางแปลงค่า
    trans_table = str.maketrans(normal_chars, fancy_chars)
    
    # ทำการแปลงข้อความ
    transformed_text = text.translate(trans_table)
    
    # ส่งข้อความที่แปลงแล้วกลับไป (แบบไม่ Ephemeral เพื่อให้คนอื่นเห็นด้วย)
    await interaction.response.send_message(transformed_text)

# ==========================================
#      🛡️ [ระบบรวม: Anti-Alt + Badwords + Ranking]
# ==========================================

# --- 1. ระบบกันไอดีสมัครใหม่ (Anti-Alt) ---
@bot.tree.command(name="set_anti_alt", description="🚫 ตั้งค่าอายุไอดีขั้นต่ำก่อนเข้าเซิร์ฟ")
@app_commands.describe(days="จำนวนวันขั้นต่ำที่สมัคร (พิมพ์ 0 เพื่อปิด)")
async def set_anti_alt(interaction: discord.Interaction, days: int):
    if not bot.check_admin(interaction): return
    bot.save_data(interaction.guild.id, "anti_alt_days", days)
    msg = f"✅ ตั้งค่าอายุไอดีขั้นต่ำ: **{days} วัน**" if days > 0 else "🚫 ปิดระบบกันไอดีสมัครใหม่"
    await interaction.response.send_message(msg, ephemeral=True)

# --- 2. ระบบคำหยาบ (Badwords) ---
@bot.tree.command(name="set_badwords", description="🤬 ตั้งค่ารายการคำหยาบที่ต้องการบล็อก")
@app_commands.describe(words="ระบุคำหยาบ (ใช้ , คั่น เช่น: คำ1,คำ2)")
async def set_badwords(interaction: discord.Interaction, words: str):
    if not bot.check_admin(interaction): return
    word_list = [w.strip().lower() for w in words.split(",")]
    bot.save_data(interaction.guild.id, "bad_words", word_list)
    await interaction.response.send_message(f"✅ บันทึกคำหยาบเรียบร้อย! (ทั้งหมด {len(word_list)} คำ)", ephemeral=True)

# ==========================================
#      📊 [ระบบเลเวล All-in-One + ปุ่มกดเช็คแต้ม - แบบถาวร]
# ==========================================

# 🔘 1. คลาสสำหรับปุ่มกด (Persistent View)
class XPCheckView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None) # ✅ ตั้งค่าเป็น None เพื่อให้ปุ่มอมตะ

    @discord.ui.button(
        label="📊 เช็คแต้ม & เลเวลของฉัน", 
        style=discord.ButtonStyle.success, 
        custom_id="check_xp_btn_fixed" # ✅ ใช้ ID ที่แน่นอนเพื่อให้บอทจำได้หลัง Restart
    )
    async def check_xp(self, interaction: discord.Interaction, button: discord.ui.Button):
        # ดึงข้อมูลจากฐานข้อมูล
        lv_data = bot.load_data(interaction.guild.id, "levels") or {}
        user_data = lv_data.get(str(interaction.user.id), {"xp": 0, "lv": 1})
        
        current_lv = user_data.get('lv', 1)
        current_xp = user_data.get('xp', 0)
        xp_needed = current_lv * 100
        
        # ป้องกันการหารด้วย 0
        progress_ratio = current_xp / xp_needed if xp_needed > 0 else 0
        progress = int(progress_ratio * 10)
        bar = "🟩" * progress + "⬜" * (10 - progress)
        
        embed = discord.Embed(
            title=f"✨ ข้อมูลระดับของ {interaction.user.display_name}", 
            color=0x2ecc71,
            description=f"แต้มของคุณจะถูกบันทึกทุกครั้งที่มีการพิมพ์ข้อความ"
        )
        embed.add_field(name="⭐ Level", value=f"` {current_lv} `", inline=True)
        embed.add_field(name="✨ XP", value=f"` {current_xp} / {xp_needed} `", inline=True)
        embed.add_field(name="📈 Progress", value=f"{bar} ({int(progress_ratio * 100)}%)", inline=False)
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

# ⚙️ 2. คำสั่งตั้งค่าระบบเลเวล
@bot.tree.command(name="level_config", description="⚙️ ตั้งค่าระบบเลเวล: แต้มต่อข้อความ, ช่องปุ่มเช็คแต้ม, และรางวัล")
@app_commands.describe(
    xp_per_msg="แต้มที่ได้รับต่อ 1 ข้อความ",
    button_channel="ห้องที่จะส่งปุ่มกดเช็คแต้มไปวาง",
    reward_level="เลเวลที่จะแจกยศ",
    reward_role="ยศที่จะได้รับ"
)
async def level_config(
    interaction: discord.Interaction, 
    xp_per_msg: int, 
    button_channel: discord.TextChannel,
    reward_level: int,
    reward_role: discord.Role
):
    if not bot.check_admin(interaction): 
        return await interaction.response.send_message("❌ คุณไม่มีสิทธิ์เข้าถึงคำสั่งนี้", ephemeral=True)

    gid = interaction.guild.id
    
    # บันทึกตั้งค่า
    bot.save_data(gid, "xp_per_msg", xp_per_msg)
    rewards = bot.load_data(gid, "level_rewards") or {}
    rewards[str(reward_level)] = reward_role.id
    bot.save_data(gid, "level_rewards", rewards)

    # ส่งปุ่มเช็คแต้มไปยังช่องที่กำหนด
    embed = discord.Embed(
        title="🏆 ระบบเลเวล NECESSARY",
        description="กดปุ่มด้านล่างเพื่อตรวจสอบแต้มและเลเวลปัจจุบันของคุณ!\n(ข้อมูลจะอัปเดตทุกครั้งที่คุณพิมพ์ข้อความ)",
        color=0x3498db
    )
    # ใช้ View ที่เป็น Persistent
    await button_channel.send(embed=embed, view=XPCheckView())

    await interaction.response.send_message(
        f"✅ **ตั้งค่าเรียบร้อย!**\n"
        f"🔹 แต้มต่อข้อความ: `{xp_per_msg}` XP\n"
        f"🔹 ปุ่มเช็คแต้มถูกส่งไปที่: {button_channel.mention}\n"
        f"🔹 รางวัล: เลเวล `{reward_level}` รับยศ {reward_role.mention}", 
        ephemeral=True
    )

# --- ⚙️ ฟังก์ชันทำงานอัตโนมัติ (Events) ---
@bot.event
async def on_member_join(member):
    # เช็ค Anti-Alt
    days_limit = bot.load_data(member.guild.id, "anti_alt_days") or 0
    if days_limit > 0:
        account_age = (datetime.datetime.now(datetime.timezone.utc) - member.created_at).days
        if account_age < days_limit:
            try:
                await member.send(f"⚠️ ไอดีของคุณอายุไม่ถึง {days_limit} วัน")
                return await member.kick(reason="Anti-Alt")
            except: pass

# --- 📊 [4] Server List Section (Owner Only) ---

@bot.tree.command(name="server_list", description="ดูรายชื่อเซิร์ฟเวอร์ (สำหรับเจ้าของ)")
async def server_list(interaction: discord.Interaction):
    if interaction.user.id != OWNER_ID:
        return await interaction.response.send_message("❌ เฉพาะเจ้าของบอทเท่านั้น", ephemeral=True)
    
    # 1. เพิ่มบรรทัดนี้ เพื่อบอก Discord ว่า "ขอเวลาประมวลผลหน่อย" (หน้าจอจะขึ้น Bot is thinking...)
    # วิธีนี้จะยืดเวลาจาก 3 วินาที เป็น 15 นาที
    await interaction.response.defer(ephemeral=True)
    
    embed = discord.Embed(title="🌐 รายชื่อเซิร์ฟเวอร์ที่บอทอยู่", color=0xf1c40f)
    
    for guild in bot.guilds:
        invite_link = "ไม่มีสิทธิ์สร้างลิงก์"
        try:
            # พยายามหาช่องที่บอทส่งข้อความได้เพื่อสร้างลิงก์
            target_channel = guild.system_channel or next((ch for ch in guild.text_channels if ch.permissions_for(guild.me).create_instant_invite), None)
            if target_channel:
                invite = await target_channel.create_invite(max_age=300)
                invite_link = f"[คลิกเพื่อเข้า]({invite.url})"
        except:
            pass

        embed.add_field(
            name=f"📛 {guild.name}",
            value=f"🆔 `{guild.id}`\n👥 สมาชิก: {guild.member_count}\n🔗 {invite_link}",
            inline=False
        )
    
    # 2. เปลี่ยนจาก interaction.response.send_message เป็น interaction.followup.send
    # เพราะเราสั่ง defer ไปแล้ว ต้องใช้ followup แทนครับ
    await interaction.followup.send(embed=embed)

# --- 🔑 [5] System & Help Section ---

@bot.tree.command(name="help", description="ดูคู่มือคำสั่งทั้งหมดของบอท NECESSARY")
async def help_cmd(interaction: discord.Interaction):
    # ตรวจสอบสิทธิ์เบื้องต้น
    if not bot.check_admin(interaction): 
        return await interaction.response.send_message("❌ เฉพาะแอดมินเท่านั้นที่ดูคู่มือนี้ได้", ephemeral=True)
    
    embed = discord.Embed(
        title="📋 คู่มือการใช้งานบอท NECESSARY (Full Update 2026)", 
        description=(
            "**⚠️ ข้อแนะนำสำคัญ:**\n"
            "โปรดตรวจสอบว่ายศของบอทอยู่ **สูงกว่า** ยศของสมาชิกทั่วไป\n"
            "เพื่อให้ระบบลงโทษ (Timeout/Kick/Ban) ทำงานได้ปกติครับ"
        ),
        color=0x3498db,
        timestamp=datetime.datetime.now()
    )
    
    # --- [1] หมวดระบบและชุมชน (System & Community) ---
    embed.add_field(name="🖥️ หมวดระบบและชุมชน", value=(
        "• `/full_status` : **[ดูทั้งหมด]** เช็คการตั้งค่าทุกอย่างในเซิร์ฟแบบละเอียด (Ticket, ต้อนรับ, ป้องกัน, แต้ม)\n"
        "• `/admin_grant` : จัดการสิทธิ์แอดมินบอท (Add/Remove)\n"
        "• `/level_config` : **[ตั้งค่าเลเวล]** กำหนดแต้มต่อข้อความ, ตั้งห้องโชว์อันดับเรียลไทม์ และยศรางวัลเมื่อเลเวลถึง\n"
        "• `/fancy_text` : แปลงข้อความเป็นตัวอักษรพิเศษ"
    ), inline=False)

    # --- [2] หมวดความปลอดภัย (Security & Moderation) ---
    embed.add_field(name="🛡️ หมวดความปลอดภัย (Security)", value=(
        "• `/anti_link` : กันส่งลิงก์ภายนอก (เลือกเวลา Timeout ได้)\n"
        "• `/anti_promo` : กันส่งลิงก์เชิญเซิร์ฟเวอร์อื่น\n"
        "• `/anti_spam` : กันพิมพ์ข้อความรัว (5 ข้อความ/5 วินาที)\n"
        "• `/set_badwords` : ตั้งค่ารายการคำหยาบที่ต้องการบล็อก\n"
        "• `/set_anti_alt` : ตั้งอายุไอดีขั้นต่ำก่อนเข้าเซิร์ฟ\n"
        "• `/anti_off` : เลือกปิดระบบการป้องกันที่ต้องการ\n"
        "• `/whitelist_add` : เพิ่ม คน/ยศ/ช่อง ที่ได้รับข้อยกเว้น"
    ), inline=False)

    # --- [3] หมวดบริการ (Services) ---
    embed.add_field(name="⚙️ หมวดบริการ (Services)", value=(
        "• `/ticket_setup` : ตั้งค่าระบบ Ticket (ล็อคสิทธิ์เจ้าของบอทแล้ว)\n"
        "• `/ticket_send` : ส่งปุ่มกดเปิด Ticket ไปยังช่องที่ต้องการ\n"
        "• `/role_setup` : ตั้งค่าปุ่มรับยศอัตโนมัติ\n"
        "• `/set_level_role` : ตั้งค่ารางวัลยศที่จะแจกตามเลเวล\n"
        "• `/webhook` : จัดการประกาศผ่าน Webhook ปลอมชื่อ/รูปได้"
    ), inline=False)

    # --- [4] หมวดต้อนรับ (Welcome) ---
    embed.add_field(name="👋 หมวดต้อนรับ (Welcome)", value=(
        "• `/set_welcome` : ตั้งค่าห้องและข้อความ (ใช้ {user}, {guild}, {count})\n"
        "• `/test_welcome` : ทดสอบส่งข้อความต้อนรับจำลอง"
    ), inline=False)
    
    # --- [5] หมวดเจ้าของบอท (Owner Only) ---
    if interaction.user.id == OWNER_ID:
        embed.add_field(name="👑 หมวดเจ้าของ (Owner Only)", value=(
            "• `/server_list` : ดูรายชื่อเซิร์ฟเวอร์ทั้งหมดที่บอทอยู่\n"
            "• `/broadcast` : ประกาศข้อความไปยังทุกเซิร์ฟเวอร์"
        ), inline=False)
    
    embed.set_footer(text=f"Requested by {interaction.user.name} | Necessary Bot 2026", icon_url=interaction.user.display_avatar.url)
    
    if interaction.guild.icon:
        embed.set_thumbnail(url=interaction.guild.icon.url)

    await interaction.response.send_message(embed=embed, ephemeral=True)

# --- 📢 [6] Broadcast System (Owner Only) ---

@bot.tree.command(name="broadcast", description="ประกาศข้อความไปยังทุกเซิร์ฟเวอร์ที่บอทอยู่ (เฉพาะเจ้าของบอท)")
async def broadcast(interaction: discord.Interaction, message: str):
    # ตรวจสอบสิทธิ์เจ้าของบอทเท่านั้น
    if interaction.user.id != OWNER_ID:
        return await interaction.response.send_message("❌ คำสั่งนี้สงวนไว้สำหรับเจ้าของบอทเท่านั้น", ephemeral=True)
    
    await interaction.response.defer(ephemeral=True)
    count = 0
    target_name = "ประกาศ-necessary"
    
    for guild in bot.guilds:
        try:
            channel = discord.utils.get(guild.text_channels, name=target_name)
            if not channel:
                overwrites = {
                    guild.default_role: discord.PermissionOverwrite(send_messages=False, view_channel=True),
                    guild.me: discord.PermissionOverwrite(send_messages=True, manage_channels=True)
                }
                channel = await guild.create_text_channel(name=target_name, overwrites=overwrites)
            
            embed = discord.Embed(
                title="📢 ประกาศจากระบบ NECESSARY",
                description=message,
                color=0xffffff, # สีขาวตามที่สั่ง
                timestamp=datetime.datetime.now()
            )
            embed.set_footer(text="Official Broadcast • Necessary Bot")
            
            await channel.send(embed=embed)
            count += 1
        except:
            continue
            
    await interaction.followup.send(f"✅ ประกาศเรียบร้อยแล้ว {count} เซิร์ฟเวอร์ (Embed สีขาว)", ephemeral=True)

# --- 🔗 [7] Webhook Management (Admin & Granted Users) ---

@bot.tree.command(name="webhook", description="จัดการ Webhook ในห้องนี้ (สำหรับแอดมิน)")
@app_commands.choices(action=[
    app_commands.Choice(name="สร้าง Webhook", value="create"),
    app_commands.Choice(name="ลบ Webhook ทั้งหมด", value="delete"),
    app_commands.Choice(name="เปลี่ยนชื่อ Webhook", value="rename")
])
async def webhook_manager(interaction: discord.Interaction, action: str, name: str = "Necessary Webhook"):
    # ใช้ระบบเช็คแอดมินเดิมของบอท (แอดมินดิส หรือ คนที่ได้ admin_grant)
    if not bot.check_admin(interaction): 
        return await interaction.response.send_message("❌ คุณไม่มีสิทธิ์จัดการ Webhook", ephemeral=True)
    
    await interaction.response.defer(ephemeral=True)
    
    try:
        if action == "create":
            webhook = await interaction.channel.create_webhook(name=name)
            await interaction.followup.send(f"✅ สร้าง Webhook สำเร็จ!\nชื่อ: `{name}`\nURL: `{webhook.url}`", ephemeral=True)
            
        elif action == "delete":
            webhooks = await interaction.channel.webhooks()
            if not webhooks:
                return await interaction.followup.send("❌ ไม่พบ Webhook ในห้องนี้", ephemeral=True)
            for wh in webhooks:
                await wh.delete()
            await interaction.followup.send(f"🗑️ ลบ Webhooks ทั้งหมดในห้องนี้เรียบร้อย", ephemeral=True)
            
        elif action == "rename":
            webhooks = await interaction.channel.webhooks()
            if not webhooks:
                return await interaction.followup.send("❌ ไม่พบ Webhook ให้เปลี่ยนชื่อ", ephemeral=True)
            
            old_name = webhooks[0].name
            await webhooks[0].edit(name=name)
            await interaction.followup.send(f"📝 เปลี่ยนชื่อจาก `{old_name}` เป็น `{name}` สำเร็จ", ephemeral=True)
            
    except Exception as e:
        await interaction.followup.send(f"❌ เกิดข้อผิดพลาด: {e}", ephemeral=True)

@bot.tree.command(name="full_status", description="🔎 รายงานสถานะเซิร์ฟเวอร์และการตั้งค่าบอทแบบละเอียดที่สุด")
async def full_status(interaction: discord.Interaction):
    if not bot.check_admin(interaction): 
        return await interaction.response.send_message("❌ เฉพาะแอดมินเท่านั้นที่ดูข้อมูลนี้ได้", ephemeral=True)
    
    gid = interaction.guild.id
    guild = interaction.guild
    embed = discord.Embed(
        title=f"📊 ข้อมูลสถานะ: {guild.name}", 
        color=0x2ecc71,
        timestamp=datetime.datetime.now()
    )

    # --- 🌐 1. ข้อมูลเซิร์ฟเวอร์ (Server Information) ---
    owner = guild.owner.mention if guild.owner else "ไม่พบข้อมูล"
    created_at = guild.created_at.strftime("%d/%m/%Y")
    
    # นับจำนวนคนแยกประเภท
    total_members = guild.member_count
    bots = sum(member.bot for member in guild.members)
    humans = total_members - bots
    
    server_info = (
        f"👑 **เจ้าของ:** {owner}\n"
        f"📅 **สร้างเมื่อ:** `{created_at}`\n"
        f"👥 **สมาชิก:** `{total_members}` (คน: `{humans}` | บอท: `{bots}`)\n"
        f"💎 **Boost:** Level `{guild.premium_tier}` (`{guild.premium_subscription_count}` บูส)\n"
        f"🛡️ **ความปลอดภัย:** `{str(guild.verification_level).upper()}`\n"
        f"📍 **ห้อง:** `{len(guild.channels)}` ช่อง | **ยศ:** `{len(guild.roles)}` ยศ"
    )
    embed.add_field(name="🌐 ข้อมูลเซิร์ฟเวอร์", value=server_info, inline=False)

    # --- 🛡️ 2. ระบบความปลอดภัย (Security Settings) ---
    sec_info = []
    l_data = bot.load_data(gid, "security_link")
    sec_info.append(f"🔗 **กันลิงก์:** {'✅' if l_data else '❌'} " + (f"({l_data.get('penalty')} | {l_data.get('timeout_mins')}m)" if l_data else ""))
    
    p_data = bot.load_data(gid, "security_promo")
    sec_info.append(f"📢 **กันโปรโมท:** {'✅' if p_data else '❌'} " + (f"({p_data.get('penalty')} | {p_data.get('timeout_mins')}m)" if p_data else ""))
    
    s_data = bot.load_data(gid, "security_spam")
    sec_info.append(f"⌨️ **กันสแปม:** {'✅' if s_data else '❌'} " + (f"({s_data.get('penalty')} | {s_data.get('timeout_mins')}m)" if s_data else ""))
    
    anti_alt = bot.load_data(gid, "anti_alt_days") or 0
    sec_info.append(f"👶 **Anti-Alt:** {f'✅ {anti_alt} วัน' if anti_alt > 0 else '❌ ปิด'}")
    
    bad_words = bot.load_data(gid, "bad_words") or []
    sec_info.append(f"🤬 **คำหยาบ:** `{len(bad_words)}` คำ")

    embed.add_field(name="🛡️ ระบบความปลอดภัย", value="\n".join(sec_info), inline=True)

    # --- 📊 3. ระบบเลเวล & รางวัล (Ranking & Rewards) ---
    lv_data = bot.load_data(gid, "levels") or {}
    rewards = bot.load_data(gid, "level_rewards") or {}
    xp_msg = bot.load_data(gid, "xp_per_msg") or 10
    
    reward_list = []
    if rewards:
        for lv, r_id in sorted(rewards.items(), key=lambda x: int(x[0])):
            role = guild.get_role(int(r_id))
            reward_list.append(f"• Lv.{lv} → {role.mention if role else 'ไม่พบ'}")
    
    rank_text = (
        f"✨ **แต้ม/ข้อความ:** `{xp_msg} XP`\n"
        f"👥 **คนมีแต้ม:** `{len(lv_data)}` คน\n"
        f"🎁 **รางวัลยศ:** " + (f"{len(reward_list)} ระดับ" if reward_list else "❌")
    )
    embed.add_field(name="📊 เลเวล & รางวัล", value=rank_text, inline=True)

    # --- ⚙️ 4. ระบบบริการ (Ticket & Self-Role) ---
    tk = bot.load_data(gid, "ticket") or {}
    rl = bot.load_data(gid, "self_role") or {}
    
    serv_info = []
    if tk:
        serv_info.append(f"🎫 **Ticket:** ✅ (<@&{tk.get('admin_role_id')}>)")
    else:
        serv_info.append(f"🎫 **Ticket:** ❌")

    if rl:
        s_role = guild.get_role(rl.get('role_id'))
        serv_info.append(f"🎭 **รับยศ:** ✅ ({s_role.mention if s_role else '❌'})")
    else:
        serv_info.append(f"🎭 **รับยศ:** ❌")

    embed.add_field(name="⚙️ ระบบบริการ", value="\n".join(serv_info), inline=True)

    # --- 🔑 5. สิทธิ์การเข้าถึง & ต้อนรับ ---
    adm_data = bot.load_data(gid, "admins") or {"users": [], "roles": []}
    wl_data = bot.load_data(gid, "whitelist") or {"channels": [], "members": []}
    wel = bot.load_data(gid, "welcome") or {}

    access_text = (
        f"🔑 **Admin บอท:** `{len(adm_data['users'])}` คน | `{len(adm_data['roles'])}` ยศ\n"
        f"🏳️ **Whitelist:** `{len(wl_data['members'])}` คน | `{len(wl_data['channels'])}` ช่อง\n"
        f"👋 **ต้อนรับ:** {'✅ เปิด' if wel else '❌ ปิด'}"
    )
    embed.add_field(name="🔑 การจัดการ & การเข้าถึง", value=access_text, inline=False)

    if guild.icon:
        embed.set_thumbnail(url=guild.icon.url)
    
    embed.set_footer(text=f"Requested by {interaction.user.name} | Necessary Bot", icon_url=interaction.user.display_avatar.url)
    
    await interaction.response.send_message(embed=embed, ephemeral=True)

# --- 🧹 [คำสั่งรีเซ็ตคะแนนแบบเลือกคน] ---
@bot.tree.command(name="level_reset", description="🧹 รีเซ็ตแต้มและเลเวลของสมาชิก (เลือกรายคน)")
@app_commands.describe(target="เลือกสมาชิกที่ต้องการรีเซ็ตคะแนน")
async def level_reset(interaction: discord.Interaction, target: discord.Member):
    # 1. เช็คสิทธิ์แอดมิน
    if not bot.check_admin(interaction):
        return await interaction.response.send_message("❌ คุณไม่มีสิทธิ์ใช้งานคำสั่งนี้", ephemeral=True)

    # 2. โหลดข้อมูล
    lv_data = bot.load_data(interaction.guild.id, "levels") or {}
    uid = str(target.id)

    # 3. ตรวจสอบว่ามีข้อมูลคนนี้ไหม
    if uid not in lv_data:
        return await interaction.response.send_message(f"❓ ไม่พบข้อมูลคะแนนของ {target.display_name} ในระบบ", ephemeral=True)

    # 4. ทำการรีเซ็ต
    lv_data[uid] = {"xp": 0, "lv": 1}
    
    # 5. บันทึกข้อมูลกลับ
    bot.save_data(interaction.guild.id, "levels", lv_data)

    # 6. แจ้งเตือน
    embed = discord.Embed(
        title="🧹 รีเซ็ตคะแนนสำเร็จ",
        description=f"ล้างข้อมูลคะแนนของ {target.mention} เรียบร้อยแล้ว\nตอนนี้กลับไปที่ **Level 1 (0 XP)**",
        color=0xff0000 # สีแดงแจ้งเตือน
    )
    embed.set_footer(text=f"จัดการโดย {interaction.user.name}")
    
    await interaction.response.send_message(embed=embed)

    # (Optional) ลอง Print ดูใน Console เพื่อยืนยัน
    print(f"DEBUG: {interaction.user.name} ได้ทำการรีเซ็ตคะแนนของ {target.name}")

# ==========================================
#      🛡️ [ระบบตรวจสอบและลงโทษ - ฉบับแก้ไขจบปัญหา]
# ==========================================

async def apply_penalty(member: discord.Member, penalty_type: str, reason: str, duration: int = 60):
    try:
        # --- ✉️ ส่ง DM เตือนก่อนโดนลงโทษ ---
        time_label = f"{duration // 60} นาที" if duration < 3600 else f"{duration // 3600} ชั่วโมง"
        embed_dm = discord.Embed(title=f"⚠️ แจ้งเตือนจาก {member.guild.name}", color=0xff0000)
        embed_dm.description = f"คุณถูกลงโทษเนื่องจาก: **{reason}**"
        embed_dm.add_field(name="บทลงโทษ", value=f"`{penalty_type.upper()}`")
        if penalty_type == "timeout":
            embed_dm.add_field(name="ระยะเวลา", value=time_label)
        try:
            await member.send(embed=embed_dm)
        except: pass

        # --- ⚖️ ดำเนินการลงโทษจริง ---
        if penalty_type == "timeout":
            await member.timeout(datetime.timedelta(seconds=duration), reason=reason)
        elif penalty_type == "ban":
            await member.ban(reason=reason, delete_message_days=1)
        print(f"✅ ลงโทษ {member.name} สำเร็จ ({penalty_type})")
    except Exception as e:
        print(f"❌ ลงโทษไม่ได้ (เช็คยศบอท): {e}")

# --- [ ✉️ รวมระบบ on_message: ตรวจความปลอดภัย + เพิ่มแต้มเลเวล (เวอร์ชันรองรับ Whitelist หมวดหมู่) ] ---
@bot.event
async def on_message(message):
    # 1. ข้ามถ้าเป็นบอท หรือคุยใน DM
    if message.author.bot or not message.guild: 
        return

    # 2. ส่วนเพิ่มแต้มเลเวล
    uid = str(message.author.id)
    gid = message.guild.id
    
    xp_gain_config = bot.load_data(gid, "xp_per_msg")
    xp_gain = int(xp_gain_config) if xp_gain_config else 10 
    lv_data = bot.load_data(gid, "levels") or {}
    
    if uid not in lv_data:
        lv_data[uid] = {"xp": 0, "lv": 1}
    
    lv_data[uid]["xp"] += xp_gain
    
    # เช็คเลเวลอัป
    xp_needed = lv_data[uid]["lv"] * 100
    if lv_data[uid]["xp"] >= xp_needed:
        lv_data[uid]["lv"] += 1
        lv_data[uid]["xp"] = 0
        try: await message.channel.send(f"🎊 ยินดีด้วย {message.author.mention}! เลเวลอัปเป็น **{lv_data[uid]['lv']}**", delete_after=10)
        except: pass

        rewards = bot.load_data(gid, "level_rewards") or {}
        role_id = rewards.get(str(lv_data[uid]["lv"]))
        if role_id:
            role = message.guild.get_role(int(role_id))
            if role:
                try: await message.author.add_roles(role)
                except: pass

    bot.save_data(gid, "levels", lv_data)

    # --------------------------------------------------
    # 3. ส่วนตรวจสอบความปลอดภัย (ข้ามถ้าเป็นแอดมินหรือไวท์ลิสต์)
    # --------------------------------------------------
    if bot.check_admin(message):
        await bot.process_commands(message)
        return

    # ✅ แก้ไขตรงนี้: เพิ่มการเช็ค Whitelist หมวดหมู่ (Categories)
    wl_data = bot.load_data(gid, "whitelist") or {"channels": [], "members": [], "categories": []}
    
    is_whitelisted = (
        message.author.id in wl_data.get("members", []) or 
        message.channel.id in wl_data.get("channels", []) or 
        (message.channel.category and message.channel.category.id in wl_data.get("categories", [])) # <--- เช็คหมวดหมู่
    )

    if is_whitelisted:
        await bot.process_commands(message)
        return

    # --- เริ่มการตรวจสอบความปลอดภัย ---
    # ตรวจสอบคำหยาบ
    bad_words = bot.load_data(gid, "bad_words") or []
    if any(w in message.content.lower() for w in bad_words):
        try: 
            await message.delete()
            return 
        except: pass

    content = message.content.lower()
    
    # ตรวจสอบโปรโมท
    p_data = bot.load_data(gid, "security_promo")
    if p_data and 'penalty' in p_data:
        if re.search(r"(discord\.gg\/|discord\.com\/invite\/)", content):
            return await process_security_violation(message, p_data, "ส่งลิงก์เชิญ (Promo)")

    # ตรวจสอบลิงก์ภายนอก
    l_data = bot.load_data(gid, "security_link")
    if l_data and 'penalty' in l_data:
        if re.search(r"(https?:\/\/[^\s]+)|(www\.[^\s]+)", content):
            if "discord.com" not in content and "discord.gg" not in content:
                return await process_security_violation(message, l_data, "ส่งลิงก์ภายนอก (Link)")

    # ตรวจสอบสแปม
    s_data = bot.load_data(gid, "security_spam")
    if s_data and 'penalty' in s_data:
        u_spam_id = f"{gid}-{message.author.id}"
        now = datetime.datetime.now()
        if u_spam_id not in bot.spam_control: bot.spam_control[u_spam_id] = []
        bot.spam_control[u_spam_id] = [t for t in bot.spam_control[u_spam_id] if (now - t).total_seconds() < 5]
        bot.spam_control[u_spam_id].append(now)
        if len(bot.spam_control[u_spam_id]) > 5:
            return await process_security_violation(message, s_data, "สแปมข้อความรัว (Spam)")

    # รันคำสั่ง Prefix (!) ปกติ
    await bot.process_commands(message)

# บรรทัดสุดท้ายของไฟล์จริงๆ
bot.run(TOKEN)
