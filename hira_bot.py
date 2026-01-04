import nextcord
from nextcord.ext import commands
import asyncio
import yt_dlp as youtube_dl
import os

# 🔊 Opus 로딩
if not nextcord.opus.is_loaded():
    try:
        nextcord.opus.load_opus("libopus.so.0")
    except Exception as e:
        print("Opus load failed:", e)
print("Opus loaded:", nextcord.opus.is_loaded())

# ===== 인텐트 설정 =====
intents = nextcord.Intents.default()
intents.message_content = True
intents.voice_states = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ===== 봇 준비 이벤트 =====
@bot.event
async def on_ready():
    print(f'로그인 성공! {bot.user} 님이 온라인 상태입니다.')
    await bot.change_presence(
        status=nextcord.Status.online,
        activity=nextcord.Game(name="음악 재생중 🎵")
    )

# ===== 기본 명령어 =====
@bot.command()
async def 따라하기(ctx, *, text):
    await ctx.send(text)

@bot.command(aliases=['입장'])
async def 들어와(ctx):
    if ctx.author.voice and ctx.author.voice.channel:
        await ctx.author.voice.channel.connect()
        await ctx.send("음성 채널에 연결되었습니다.")
    else:
        await ctx.send("❌ 먼저 음성 채널에 들어가 주세요.")

@bot.command(aliases=['나가','퇴장'])
async def out(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("음성 채널에서 퇴장했습니다.")
    else:
        await ctx.send("❌ 봇이 음성 채널에 없습니다.")

# ===== yt-dlp / FFmpeg 설정 =====
ydl_opts = {
    'format': 'bestaudio/best',  # 오디오만 가져오는 설정
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '192',
    }],
    'cookiefile': 'cookies.txt', 
}
ffmpeg_opts = {
    "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
    "options": "-vn",
}

ytdl = youtube_dl.YoutubeDL(ytdl_opts)

class YTDLSource(nextcord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get("title")
        self.url = data.get("url")

    @classmethod
    async def from_url(cls, url, *, loop):
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=False))
        if data is None:
            raise RuntimeError("yt-dlp 정보 추출 실패")
        if "entries" in data:
            data = data["entries"][0]
        return cls(nextcord.FFmpegPCMAudio(data["url"], **ffmpeg_opts), data=data)

# ===== 음악 Cog =====
class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.queue = []
        self.MAX_QUEUE = 10

    async def play_next(self, ctx):
        if self.queue:
            player = self.queue.pop(0)
            ctx.voice_client.play(player, after=lambda e: asyncio.run_coroutine_threadsafe(self.play_next(ctx), self.bot.loop))
            await ctx.send(f"🎵 재생중: **{player.title}**")
        else:
            await asyncio.sleep(60)
            if ctx.voice_client and not ctx.voice_client.is_playing():
                await ctx.voice_client.disconnect()
                await ctx.send("대기열이 비어 있어 퇴장합니다 👋")

    @commands.command(aliases=["노래"])
    async def play(self, ctx, *, url):
        if not ctx.voice_client:
            if not ctx.author.voice:
                await ctx.send("❌ 음성 채널에 먼저 들어가 주세요.")
                return
            await ctx.author.voice.channel.connect()
        if len(self.queue) >= self.MAX_QUEUE:
            await ctx.send("❌ 대기열이 가득 찼습니다.")
            return
        async with ctx.typing():
            try:
                player = await YTDLSource.from_url(url, loop=self.bot.loop)
            except Exception as e:
                await ctx.send(f"❌ 음악 로드 실패: {e}")
                return
        vc = ctx.voice_client
        if vc.is_playing():
            self.queue.append(player)
            await ctx.send(f"➕ 대기열 추가: **{player.title}**")
        else:
            vc.play(player, after=lambda e: asyncio.run_coroutine_threadsafe(self.play_next(ctx), self.bot.loop))
            await ctx.send(f"🎶 재생 시작: **{player.title}**")

    @commands.command(aliases=["스킵"])
    async def skip(self, ctx):
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.stop()
            await ctx.send("⏭ 다음 곡으로 이동")
        else:
            await ctx.send("❌ 재생 중인 곡이 없습니다.")

    @commands.command(aliases=["중지"])
    async def pause(self, ctx):
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.pause()
            await ctx.send("⏸ 일시 정지")
        else:
            await ctx.send("❌ 재생 중이 아닙니다.")

    @commands.command(aliases=["재생"])
    async def resume(self, ctx):
        if ctx.voice_client and ctx.voice_client.is_paused():
            ctx.voice_client.resume()
            await ctx.send("▶ 재생 재개")
        else:
            await ctx.send("❌ 일시 정지 상태가 아닙니다.")

    @commands.command(aliases=["목록"])
    async def queue_list(self, ctx):
        if not self.queue:
            await ctx.send("📭 대기열이 비어 있습니다.")
            return
        msg = "\n".join(f"{i+1}. {song.title}" for i, song in enumerate(self.queue))
        await ctx.send(f"🎵 대기열:\n{msg}")

bot.add_cog(Music(bot))

# ===== 봇 실행 =====
access_token = os.environ["DISCORD_TOKEN"]
bot.run(access_token)

