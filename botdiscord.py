import discord
from discord.ext import commands, tasks
import json
import os
os.system("pip install PyNaCl discord.py[voice]")
from datetime import datetime, timezone, timedelta, time
import aiohttp
import xml.etree.ElementTree as ET
from flask import Flask
from threading import Thread
import yt_dlp
import asyncio
import imageio_ffmpeg
# --- CÀI ĐẶT WEB SERVER CHỐNG NGỦ ĐÔNG ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot Discord dang hoat dong 24/7!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

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
# --- TÍNH NĂNG PHÁT NHẠC ---

# Cấu hình yt-dlp để chỉ lấy âm thanh, chất lượng tốt nhất
ydl_opts = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'quiet': True,
}

# Cấu hình FFmpeg để stream mượt mà, tự động kết nối lại nếu mạng lag
ffmpeg_options = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn' # -vn nghĩa là "no video" (chỉ lấy âm thanh)
}
@bot.command()
async def batnhacchoanh(ctx, url: str):
    # 1. Kiểm tra phòng
    if not ctx.author.voice:
        await ctx.send("❌ Bạn phải vào một kênh thoại trước đã!")
        return
    
    voice_channel = ctx.author.voice.channel
    await ctx.send("🕵️ 1. Đã thấy bạn trong phòng, chuẩn bị mở cửa chui vào...")

    # 2. Rải máy quay ở khu vực hay kẹt nhất
    try:
        voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)
        if not voice_client:
            await ctx.send("🕵️ 2. Đang vặn tay nắm cửa (Nếu bot im lặng sau câu này thì chắc chắn lỗi mạng Render!)...")
            
            # Ép bot chỉ được cố gắng trong 10 giây, nếu không được phải báo lỗi ngay!
            voice_client = await voice_channel.connect(timeout=10.0, reconnect=False)
            
            await ctx.send("🕵️ 3. Phù! Đã chui vào phòng thành công!")
        elif voice_client.channel != voice_channel:
            await voice_client.move_to(voice_channel)
    except Exception as e:
        await ctx.send(f"❌ Kẹt cửa rồi! Lỗi chính xác là: {e}")
        return

    await ctx.send(f"⏳ Đang xử lý link YouTube... Vui lòng đợi nhé!")

    # 3. Lấy dữ liệu và phát nhạc
    try:
        loop = asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: yt_dlp.YoutubeDL(ydl_opts).extract_info(url, download=False))
        
        audio_url = data['url'] 
        title = data.get('title', 'Bài hát không tên')

        if voice_client.is_playing():
            voice_client.stop() 

        ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()
        player = discord.FFmpegPCMAudio(audio_url, executable=ffmpeg_path, **ffmpeg_options)
        voice_client.play(player)
        
        await ctx.send(f"▶️ Đang phát: **{title}**")

    except Exception as e:
        await ctx.send(f"❌ Có lỗi khi phát nhạc: {e}")

# Lệnh đuổi bot ra khỏi phòng thoại
@bot.command()
async def stop(ctx):
    voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if voice_client and voice_client.is_connected():
        await voice_client.disconnect()
        await ctx.send("👋 Bot đã tắt nhạc và rời phòng thoại!")
    else:
        await ctx.send("Bot đang không ở trong phòng thoại nào cả.")
# --- KHỞI ĐỘNG WEB SERVER VÀ BOT ---
keep_alive()
bot.run(os.getenv('DISCORD_TOKEN'))
