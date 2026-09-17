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
import requests
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
VOICE_FILE = 'voice_settings.json'

def load_voice_settings():
    if os.path.exists(VOICE_FILE):
        with open(VOICE_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_voice_settings(data):
    with open(VOICE_FILE, 'w') as f:
        json.dump(data, f, indent=4)
# ĐIỀN CÁI MÃ API BẠN VỪA COPY TRÊN WEB FPT VÀO GIỮA 2 DẤU NGOẶC KÉP NÀY:
FPT_API_KEY = "3wHXqEYr56WEJnPDN0ExQ1FS8ZndYoEe"

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
# ----------------- HỆ THỐNG QUEUE VÀ ĐIỀU KHIỂN NHẠC -----------------
music_queues = {}

async def play_next(ctx):
    guild_id = ctx.guild.id
    voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)

    if guild_id in music_queues and len(music_queues[guild_id]) > 0:
        song = music_queues[guild_id].pop(0)
        selected_url = song['url']
        selected_title = song['title']
        msg_id = song['message_id']

        await ctx.send(f"⏳ Đang chuẩn bị bài **{selected_title}**...")

        try:
            loop = asyncio.get_event_loop()
            file_name_template = f"song_{msg_id}.%(ext)s"
            play_opts = {
                'format': 'bestaudio/best',
                'outtmpl': file_name_template,
                'noplaylist': True,
            }

            await loop.run_in_executor(None, lambda: yt_dlp.YoutubeDL(play_opts).download([selected_url]))

            downloaded_files = glob.glob(f"song_{msg_id}.*")
            if not downloaded_files:
                await ctx.send("❌ Tải nhạc thất bại, tự động chuyển bài tiếp theo.")
                return await play_next(ctx)

            audio_file = downloaded_files[0]
            ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()
            
            player = discord.FFmpegPCMAudio(audio_file, executable=ffmpeg_path, stderr=sys.stderr)

            # Hàm dọn rác trễ 1 phút ở nền (vẫn giữ file trong 1 phút để phòng hờ)
            async def delayed_cleanup_and_next(file_path):
                await asyncio.sleep(60) # Chờ 60 giây
                try:
                    if os.path.exists(file_path):
                        os.remove(file_path)
                        print(f"🗑️ Đã tự động dọn rác file sau 1 phút: {file_path}")
                except Exception as e:
                    print(f"⚠️ Lỗi dọn rác ngầm: {e}")

            def check_error(error):
                if error:
                    print(f"🚨 LỖI FFMPEG: {error}")
                
                # Kích hoạt tiến trình đếm ngược 1 phút xóa file và chạy bài tiếp theo ở nền
                asyncio.run_coroutine_threadsafe(delayed_cleanup_and_next(audio_file), bot.loop)
                asyncio.run_coroutine_threadsafe(play_next(ctx), bot.loop)

            voice_client.play(player, after=check_error)
            await ctx.send(f"▶️ Đang phát: **{selected_title}** 🎧")

        except Exception as e:
            await ctx.send(f"❌ Có lỗi khi tải bài này: {e}")
            await play_next(ctx)
    else:
        await ctx.send("✅ Hàng đợi đã trống! Tạm biệt các bạn.")


# ----------------- LỆNH TÌM VÀ THÊM VÀO QUEUE -----------------
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

    guild_id = ctx.guild.id
    if guild_id not in music_queues:
        music_queues[guild_id] = []
        
    song_info = {
        'title': selected_title,
        'url': selected_url,
        'message_id': ctx.message.id
    }
    
    music_queues[guild_id].append(song_info)

    if voice_client.is_playing():
        await ctx.send(f"✅ Đã thêm vào hàng đợi: **{selected_title}** (Vị trí thứ {len(music_queues[guild_id])})")
    else:
        await play_next(ctx)


# ----------------- LỆNH SKIP (BỎ QUA BÀI HIỆN TẠI) -----------------
@bot.command()
async def skip(ctx):
    voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if voice_client and voice_client.is_playing():
        voice_client.stop() # Dừng bài hiện tại, tự động chuyển sang bài kế tiếp
        await ctx.send("⏭️ Đã bỏ qua bài hiện tại!")
    else:
        await ctx.send("❌ Hiện tại bot có đang phát bài nào đâu mà skip!")


# ----------------- LỆNH STOP (ĐUỔI BOT RA KHỎI PHÒNG) -----------------
@bot.command()
async def stop(ctx):
    voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    guild_id = ctx.guild.id
    
    # Xóa sạch hàng đợi của server này khi stop hẳn
    if guild_id in music_queues:
        music_queues[guild_id].clear()
        
    if voice_client and voice_client.is_connected():
        await voice_client.disconnect()
        await ctx.send("👋 Bot đã dừng nhạc, xóa hàng đợi và rời phòng thoại!")
    else:
        await ctx.send("Bot đang không ở trong phòng thoại nào cả.")
# ----------------- LỆNH ĐỌC VĂN BẢN (FPT.AI CAO CẤP) -----------------
@bot.command()
async def ngheanhbaonay(ctx, *, text: str):
    if not ctx.author.voice:
        await ctx.send("❌ Vào kênh thoại thì anh mới nói được chứ!")
        return
        
    voice_channel = ctx.author.voice.channel
    
    try:
        voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)
        if not voice_client:
            voice_client = await voice_channel.connect(timeout=10.0, reconnect=False)
        elif voice_client.channel != voice_channel:
            await voice_client.move_to(voice_channel)
    except Exception as e:
        await ctx.send(f"❌ Ô không, Anh mất kết lối: {e}")
        return

    if len(text) > 1200:
        await ctx.send("❌ Dài vl, viết ngắn thôi dài quá anh đéo đọc đâu")
        return

    # 1. TRA CỨU CẤU HÌNH NGƯỜI DÙNG
    settings = load_voice_settings()
    user_pref = settings.get(str(ctx.author.id), {'gender': 'nam', 'region': 'bac'})
    
    gender = user_pref['gender']
    region = user_pref['region']
    
    # 2. BẢN ĐỒ MAP VỚI CÁC GIỌNG ĐỌC CỦA FPT.AI
    voice_map = {
        'bac_nam': 'leminh',       # Lê Minh (Nam - Bắc)
        'bac_nu': 'banmai',        # Ban Mai (Nữ - Bắc)
        'nam_bo_nam': 'minhquang', # Minh Quang (Nam - Nam Bộ)
        'nam_nam': 'minhquang',    
        'nam_bo_nu': 'lannhi',     # Lan Nhi (Nữ - Nam Bộ)
        'nam_nu': 'lannhi',        
        'trung_nu': 'myan',        # Mỹ An (Nữ - Miền Trung)
        'trung_nam': 'leminh'      # FPT hạn chế Nam Miền Trung ở bản miễn phí, lấy tạm Lê Minh
    }
    
    dict_key = f"{region}_{gender}"
    fpt_voice = voice_map.get(dict_key, 'banmai')
    
    gender_txt = "Nam" if gender == 'nam' else "Nữ"
    region_txt = "Miền Bắc" if region == 'bac' else ("Miền Trung" if region == 'trung' else "Miền Nam")
    
    await ctx.send(f"🎙️ Đợi tí anh đổi giọng **{gender_txt} {region_txt}**...")

    # 3. GỬI YÊU CẦU LÊN FPT.AI
    try:
        payload = text.encode('utf-8')
        headers = {
            'api-key': FPT_API_KEY,
            'voice': fpt_voice
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post('https://api.fpt.ai/hmi/tts/v5', data=payload, headers=headers) as response:
                res_data = await response.json()
                
                if res_data.get('error') == 0:
                    audio_url = res_data.get('async')
                    
                    # Chờ máy chủ FPT tạo xong file âm thanh (kiểm tra mỗi giây)
                    speech_file = f"tts_{ctx.message.id}.mp3"
                    file_ready = False
                    
                    for _ in range(15): # Chờ tối đa 15 giây
                        await asyncio.sleep(1)
                        async with session.get(audio_url) as audio_res:
                            if audio_res.status == 200:
                                audio_content = await audio_res.read()
                                with open(speech_file, 'wb') as f:
                                    f.write(audio_content)
                                file_ready = True
                                break
                                
                    if not file_ready:
                        await ctx.send("❌ Lỗi app rồi, anh đã mất giọng")
                        return
                else:
                    await ctx.send(f"❌ Lỗi từ FPT.AI: {res_data.get('message')}")
                    return

        # 4. PHÁT FILE ÂM THANH
        if voice_client.is_playing():
            voice_client.stop()

        ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()
        player = discord.FFmpegPCMAudio(speech_file, executable=ffmpeg_path)

        def cleanup_speech(error):
            if error:
                print(f"🚨 Lỗi đọc TTS: {error}")
            try:
                if os.path.exists(speech_file):
                    os.remove(speech_file)
            except:
                pass

        voice_client.play(player, after=cleanup_speech)
    except Exception as e:
        await ctx.send(f"❌ Lỗi cmmr: {e}")
keep_alive()
bot.run(os.getenv('DISCORD_TOKEN'))
