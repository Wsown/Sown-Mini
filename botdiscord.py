import discord
from discord.ext import commands, tasks
import json
import os
from datetime import datetime, timezone, timedelta, time
import aiohttp
import xml.etree.ElementTree as ET

intents = discord.Intents.default()
intents.message_content = True
intents.members = True # Quyền nhận diện thành viên
bot = commands.Bot(command_prefix='!', intents=intents)

FILE_NAME = 'birthdays.json'

def load_bdays():
    if os.path.exists(FILE_NAME):
        with open(FILE_NAME, 'r') as f:
            return json.load(f)
    return {}

def save_bdays(data):
    with open(FILE_NAME, 'w') as f:
        json.dump(data, f, indent=4)

@bot.event
async def on_ready():
    print(f'Bot {bot.user} đã sẵn sàng!')
    check_birthdays.start()

# --- ĐÃ CẬP NHẬT: YÊU CẦU NHẬP CẢ NĂM SINH ---
@bot.command()
async def setbday(ctx, member: discord.Member, date: str):
    try:
        # Kiểm tra chuẩn Ngày/Tháng/Năm (VD: 15/09/2007)
        datetime.strptime(date, "%d/%m/%Y")
        
        data = load_bdays()
        data[str(member.id)] = date
        save_bdays(data)
        
        await ctx.send(f"✅ Đã lưu sinh nhật của {member.mention} vào ngày {date}!")
    except ValueError:
        await ctx.send("❌ Vui lòng nhập đúng định dạng Ngày/Tháng/Năm (Ví dụ: 15/09/2007)")
# --- CÀI ĐẶT MÚI GIỜ VÀ THỜI GIAN CHẠY ---
# --- CÀI ĐẶT MÚI GIỜ VÀ THỜI GIAN CHẠY ---
# Tạo múi giờ Việt Nam (UTC+7)
tz_VN = timezone(timedelta(hours=7))

# Thiết lập giờ chạy (đổi thành giờ hiện tại + 2 phút để test nhé)
midnight = time(hour=0, minute=0, second=0, tzinfo=tz_VN)

@tasks.loop(time=midnight)
async def check_birthdays():
    # NHỚ ĐỔI LẠI ID KÊNH CỦA BẠN VÀO ĐÂY NHÉ!
    channel_id = 1266443520080740392 
    channel = bot.get_channel(channel_id)
    
    if not channel:
        return

    # Lấy thời gian hiện tại
    now = datetime.now()
    today_str = now.strftime("%d/%m") # Lấy ra chuỗi "15/09" để so sánh
    current_year = now.year           # Lấy năm hiện tại để tính tuổi
    
    data = load_bdays()

    for user_id, bday_str in data.items():
        try:
            # Chuyển chuỗi "15/09/2007" thành dữ liệu ngày tháng
            bday_date = datetime.strptime(bday_str, "%d/%m/%Y")
            
            # Nếu Ngày và Tháng khớp với hôm nay
            if bday_date.strftime("%d/%m") == today_str:
                # Tính tuổi
                age = current_year - bday_date.year
                
                # Gửi lời chúc mới có tuổi
                await channel.send(f"🎉 Chúc mừng <@{user_id}> {age} tuổi thật rực rỡ! 🎂🎈")
        except ValueError:
            # Bỏ qua nếu dữ liệu bị lỗi định dạng
            pass

bot.run(os.getenv('DISCORD_TOKEN')) # Đừng quên thay Token của bạn
# --- TÍNH NĂNG THEO DÕI YOUTUBE ---
last_video_id = None 

@tasks.loop(minutes=10) 
async def check_youtube():
    global last_video_id
    
    channel_id = 123456789012345678 # Thay bằng ID kênh của bạn
    channel = bot.get_channel(channel_id)
    if not channel:
        return

    youtube_channel_id = "ĐIỀN_ID_YOUTUBE_VÀO_ĐÂY" 
    url = f"https://www.youtube.com/feeds/videos.xml?channel_id={youtube_channel_id}"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.text()
                    root = ET.fromstring(data)
                    ns = {'ns': 'http://www.w3.org/2005/Atom', 'yt': 'http://www.youtube.com/xml/schemas/2015'}
                    entry = root.find('ns:entry', ns)
                    if entry is not None:
                        video_id = entry.find('yt:videoId', ns).text
                        video_title = entry.find('ns:title', ns).text
                        video_url = entry.find('ns:link', ns).attrib['href']
                        
                        if last_video_id is None:
                            last_video_id = video_id
                        elif video_id != last_video_id:
                            last_video_id = video_id
                            await channel.send(f"🚨 **VIDEO MỚI NÈ:** {video_title}\n{video_url}")
    except Exception as e:
        print(f"Lỗi khi check YouTube: {e}")
        # --- TÍNH NĂNG THEO DÕI TIKTOK ---

# Biến nhớ link video TikTok cuối cùng
last_tiktok_url = None 

# Check mỗi 15 phút
@tasks.loop(minutes=15)
async def check_tiktok():
    global last_tiktok_url
    
    # 1. ĐIỀN ID KÊNH DISCORD VÀO ĐÂY (Giống hệt YouTube)
    channel_id = 1264626963348193353 
    channel = bot.get_channel(channel_id)
    if not channel:
        return

    # 2. ĐIỀN TÊN NGƯỜI DÙNG TIKTOK VÀO ĐÂY (Bỏ dấu @ đi nhé)
    tiktok_username = "traidepbk169" 
    
    # Dùng máy chủ ProxiTok của cộng đồng để ép TikTok ra định dạng RSS
    url = f"https://proxitok.pabloferreiro.es/@{tiktok_username}/rss"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.text()
                    
                    # Đọc dữ liệu
                    root = ET.fromstring(data)
                    
                    # Tìm video mới nhất (Trong cấu trúc này, nó nằm ở channel -> item)
                    first_item = root.find('./channel/item')
                    
                    if first_item is not None:
                        video_title = first_item.find('title').text
                        video_url = first_item.find('link').text
                        
                        # Logic kiểm tra:
                        if last_tiktok_url is None:
                            last_tiktok_url = video_url
                        elif video_url != last_tiktok_url:
                            last_tiktok_url = video_url
                            await channel.send(f"🎵 **CÓ TIKTOK MỚI NÈ:** {video_title}\n{video_url}")
    except Exception as e:
        print(f"Lỗi khi check TikTok: {e}")