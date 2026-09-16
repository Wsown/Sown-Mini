import discord
import nacl
from discord.ext import commands, tasks
import json
import os
from datetime import datetime, timezone, timedelta, time
import aiohttp
import xml.etree.ElementTree as ET
from flask import Flask
from threading import Thread
import yt_dlp
import asyncio
import imageio_ffmpeg
import sys
import glob
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
    'cookiefile': 'cookies.txt',
    'extractor_args': {
        'youtube': ['player_client=tv,mweb']
    }
}

# Cấu hình FFmpeg để stream mượt mà, tự động kết nối lại nếu mạng lag
ffmpeg_options = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn' # -vn nghĩa là "no video" (chỉ lấy âm thanh)
}
# ----------------- HỆ THỐNG DANH SÁCH CHỜ (QUEUE) -----------------
# 1. Tạo "Giỏ hàng" lưu nhạc cho từng server
music_queues = {}

# 2. Hàm tự động chuyển bài (Bộ não của Queue)
async def play_next(ctx):
    guild_id = ctx.guild.id
    voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)

    # Kiểm tra xem giỏ hàng còn bài nào không
    if guild_id in music_queues and len(music_queues[guild_id]) > 0:
        song = music_queues[guild_id].pop(0) # Rút bài đầu tiên ra
        selected_url = song['url']
        selected_title = song['title']
        msg_id = song['message_id'] # Mã riêng để không bị trùng tên file

        await ctx.send(f"⏳ Đang kéo bài **{selected_title}** về...")

        try:
            loop = asyncio.get_event_loop()
            file_name_template = f"song_{msg_id}.%(ext)s"
            play_opts = {
                'format': 'bestaudio/best',
                'outtmpl': file_name_template,
                'noplaylist': True,
            }

            # Tải nhạc bằng luồng ngầm (không làm đơ bot)
            await loop.run_in_executor(None, lambda: yt_dlp.YoutubeDL(play_opts).download([selected_url]))

            downloaded_files = glob.glob(f"song_{msg_id}.*")
            if not downloaded_files:
                await ctx.send("❌ Tải nhạc thất bại, tự động chuyển bài tiếp theo.")
                return await play_next(ctx)

            audio_file = downloaded_files[0]
            ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()
            
            player = discord.FFmpegPCMAudio(audio_file, executable=ffmpeg_path, stderr=sys.stderr)

            # Máy nghe lén: Báo lỗi, dọn rác và chuyển bài
            def check_error(error):
                if error:
                    print(f"🚨 LỖI FFMPEG: {error}")
                try:
                    os.remove(audio_file) # Dọn sạch rác đúng cái file vừa hát xong
                except:
                    pass
                # GỌI LẠI HÀM NÀY ĐỂ KÍCH HOẠT BÀI TIẾP THEO
                asyncio.run_coroutine_threadsafe(play_next(ctx), bot.loop)

            voice_client.play(player, after=check_error)
            await ctx.send(f"▶️ Đang phát: **{selected_title}** 🎧")

        except Exception as e:
            await ctx.send(f"❌ Có lỗi khi tải bài này: {e}")
            await play_next(ctx) # Lỗi thì bỏ qua, tự next bài
    else:
        await ctx.send("✅ Đã phát hết nhạc trong hàng đợi! Trả lại sự tĩnh lặng.")


# ----------------- LỆNH TÌM VÀ ĐẶT NHẠC -----------------
@bot.command()
async def batnhacchoanh(ctx, *, query: str): 
    if not ctx.author.voice:
        await ctx.send("❌ Bạn phải vào một kênh thoại trước đã!")
        return
        
    voice_channel = ctx.author.voice.channel
    
    try:
        voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)
        if not voice_client:
            voice_client = await voice_channel.connect(timeout=10.0, reconnect=False)
        elif voice_client.channel != voice_channel:
            await voice_client.move_to(voice_channel)
    except Exception as e:
        await ctx.send(f"❌ Không kết nối được kênh thoại: {e}")
        return

    await ctx.send(f"🔍 Đang tìm kiếm `{query}` trên SoundCloud...")

    search_opts = {
        'format': 'bestaudio/best',
        'noplaylist': True,
        'extract_flat': True, 
    }
    
    try:
        loop = asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: yt_dlp.YoutubeDL(search_opts).extract_info(f"scsearch5:{query}", download=False))
        
        if 'entries' not in data or not data['entries']:
            await ctx.send("❌ Không tìm thấy bài nào trên SoundCloud!")
            return
            
        entries = data['entries']
        
        menu = "**🎵 Chọn bài (1-5):**\n"
        for i, entry in enumerate(entries):
            title = entry.get('title', 'Không tên')
            menu += f"`{i+1}.` {title}\n"
            
        await ctx.send(menu)
        
        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel and m.content.isdigit()
            
        try:
            msg = await bot.wait_for('message', check=check, timeout=30.0)
            choice = int(msg.content)
            
            if choice < 1 or choice > len(entries):
                await ctx.send("❌ Số không hợp lệ, lệnh đã bị hủy.")
                return
                
            selected_entry = entries[choice - 1]
            selected_url = selected_entry.get('url')
            selected_title = selected_entry.get('title')
            
        except asyncio.TimeoutError:
            await ctx.send("⏳ Quá 30 giây không thấy bạn chọn, hủy lệnh!")
            return
            
    except Exception as e:
        await ctx.send(f"❌ Có lỗi khi tìm kiếm: {e}")
        return

    # -------- NHÉT VÀO GIỎ HÀNG --------
    guild_id = ctx.guild.id
    if guild_id not in music_queues:
        music_queues[guild_id] = [] # Khởi tạo giỏ nếu chưa có
        
    song_info = {
        'title': selected_title,
        'url': selected_url,
        'message_id': ctx.message.id # Lấy mã chat để làm tên file không bị trùng
    }
    
    music_queues[guild_id].append(song_info) # Bỏ bài hát vào giỏ

    # Nếu bot đang hát, chỉ báo xếp hàng. Nếu bot đang rảnh, gọi hàm lấy bài ra hát!
    if voice_client.is_playing():
        await ctx.send(f"✅ Đã thêm vào hàng đợi: **{selected_title}** (Vị trí thứ {len(music_queues[guild_id])})")
    else:
        await play_next(ctx)

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
