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
import urllib.parse
from bs4 import BeautifulSoup
import re
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


# ----------------- LỆNH ĐỌC VĂN BẢN (GIỌNG GOOGLE CƠ BẢN - MIỄN PHÍ 100%) -----------------
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

    status_msg = await ctx.send("🎙️ Đang dịch giọng chị Google...")

    try:
        # Chạy gTTS ở luồng ngầm để bot không bị đơ
        loop = asyncio.get_event_loop()
        speech_file = f"tts_{ctx.message.id}.mp3"
        
        def create_google_tts():
            from gtts import gTTS
            tts = gTTS(text=text, lang='vi', slow=False)
            tts.save(speech_file)
            
        await loop.run_in_executor(None, create_google_tts)

        # Dọn đường phát nhạc
        if voice_client.is_playing():
            voice_client.stop()

        ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()
        player = discord.FFmpegPCMAudio(speech_file, executable=ffmpeg_path, stderr=sys.stderr)

        def cleanup_speech(error):
            if error:
                print(f"🚨 Lỗi phát âm thanh: {error}")
            try:
                if os.path.exists(speech_file):
                    os.remove(speech_file)
            except:
                pass

        voice_client.play(player, after=cleanup_speech)
        await status_msg.edit(content="▶️ Chị Google đang đọc trong kênh thoại rồi đó!")

    except Exception as e:
        await status_msg.edit(content=f"❌ Có lỗi khi tạo giọng Google: {e}")
# ----------------- HỆ THỐNG TRA CỨU HỢP ÂM CHUẨN (BẢN PRO V2 - CHỐNG LỖI 100 KÝ TỰ) -----------------
class HopAmSelect(discord.ui.Select):
    # Khai báo thêm danh sách urls để lưu trữ link bên ngoài Menu
    def __init__(self, options, urls):
        self.urls = urls
        super().__init__(placeholder="👆 Click vào đây để chọn bài hát...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_message("⏳ Đang chép lời và căn chỉnh hợp âm cho đẹp, chờ xíu nha...", ephemeral=False)
        
        # Lấy số thứ tự (index) mà người dùng vừa click, rồi chiếu vào danh sách URL
        index = int(self.values[0])
        url = self.urls[index]
        
        try:
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    html_content = await response.text()
                    
            soup = BeautifulSoup(html_content, 'html.parser')
            lyric_element = soup.find('div', id='song-lyric')
            if not lyric_element:
                lyric_element = soup.find('div', class_='lyric-content') or soup.find('pre')
                
            if lyric_element:
                raw_html = str(lyric_element)
                raw_html = re.sub(r'</?(div|p|br)[^>]*>', '\n', raw_html)
                lines = raw_html.split('\n')
                
                final_output = []
                for line in lines:
                    if not line.strip():
                        continue
                        
                    line_soup = BeautifulSoup(line, 'html.parser')
                    chord_line = ""
                    text_line = ""
                    
                    for element in line_soup.contents:
                        if element.name == 'span' and 'chord' in element.get('class', []):
                            chord = element.text.strip()
                            while len(chord_line) < len(text_line):
                                chord_line += " "
                            chord_line += chord
                        else:
                            text = element.text if hasattr(element, 'text') else str(element)
                            text_line += text
                            
                    import html
                    text_line = html.unescape(text_line).replace('\r', '')
                    
                    if chord_line.strip():
                        final_output.append(chord_line)
                    if text_line.strip():
                        final_output.append(text_line)
                    if not chord_line.strip() and not text_line.strip():
                        final_output.append("")
                        
                text = "\n".join(final_output)
                
                chunks = [text[i:i+1900] for i in range(0, len(text), 1900)]
                for i, chunk in enumerate(chunks):
                    if i == 0:
                        await interaction.followup.send(f"🎸 **HỢP ÂM BÀI HÁT:**\n```text\n{chunk}\n```")
                    else:
                        await interaction.followup.send(f"```text\n{chunk}\n```")
            else:
                await interaction.followup.send("❌ Đã tìm thấy trang nhưng không bóc được lời bài hát.")
                
        except Exception as e:
            await interaction.followup.send(f"❌ Có lỗi khi tải bài: {e}")

class HopAmView(discord.ui.View):
    def __init__(self, select_options, urls):
        super().__init__(timeout=60)
        self.add_item(HopAmSelect(select_options, urls))

@bot.command()
async def hopam(ctx, *, query: str):
    msg = await ctx.send(f"🔍 Đang lùng sục `{query}` trên trang hợp âm...")
    
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        
        mien_chinh = "hopamchuan"
        duoi_mien = "com"
        
        url = f"https://{mien_chinh}.{duoi_mien}/search?q={urllib.parse.quote(query)}"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                html_content = await response.text()
                
        soup = BeautifulSoup(html_content, 'html.parser')
        results = []
        
        for a in soup.find_all('a', href=True):
            href = a['href']
            if '/song/' in href and not href.endswith('/song/'):
                title = a.text.strip()
                if title and len(title) > 2 and "Phiên bản" not in title and "Gửi" not in title:
                    desc = "Nhấp để xem chi tiết"
                    
                    container = a.find_parent(['div', 'li'])
                    if container:
                        all_text = " | ".join([t.strip() for t in container.stripped_strings if t.strip() and t.strip() != title])
                        if all_text:
                            desc = all_text[:95]
                    
                    if not href.startswith("http"):
                        href = f"https://{mien_chinh}.{duoi_mien}" + href
                        
                    if not any(r['url'] == href for r in results):
                        results.append({'title': title[:95], 'url': href, 'desc': desc})
            
            if len(results) >= 10:
                break
                
        if not results:
            await msg.edit(content=f"❌ Tìm nát web rồi mà không thấy bài `{query}` nào!")
            return
            
        select_options = []
        urls_list = []
        
        for i, res in enumerate(results):
            # LÁCH LUẬT DISCORD: Lưu index "0", "1", "2"... vào Menu thay vì link gốc (luôn dài < 100 ký tự)
            select_options.append(discord.SelectOption(label=res['title'], description=res['desc'], value=str(i), emoji="🎸"))
            # Nhét link thật vào một danh sách "sổ tay" riêng
            urls_list.append(res['url'])
            
        view = HopAmView(select_options, urls_list)
        await msg.edit(content=f"🎶 Tìm thấy kết quả cho `{query}` rồi đây. Chọn 1 bài nhé:", view=view)
        
    except Exception as e:
        await msg.edit(content=f"❌ Lỗi mạng rồi: {e}")
# --- KHỞI ĐỘNG WEB SERVER VÀ BOT ---
keep_alive()
bot.run(os.getenv('DISCORD_TOKEN'))
