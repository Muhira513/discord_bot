import nextcord
from nextcord.ext import commands
import asyncio
import yt_dlp as youtube_dl
import os

# ===== Opus 로딩 =====
if not nextcord.opus.is_loaded():
    try:
        nextcord.opus.load_opus("libopus.so.0")
    except Exception as e:
        print("Opus load failed:", e)

print("Opus loaded:", nextcord.opus.is_loaded())

# ===== Intents =====
intents = nextcord.Intents.default()
intents.message_content = True
intents.voice_states = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ===== Ready =====
@bot.event
async def on_ready():
    print(f"✅ 로그인 성공: {bot.user}")

# ===== yt-dlp 설정 =====
ytdl_opts = {
    "format": "bestaudio/best",
    "noplaylist": True,
    "quiet": True,
    "default_search": "auto",
    "source_address": "0.0.0.0",
}

# 🔥 cookies.txt 있으면만 사용
if os.path.exists("cookies.txt"):
    ytdl_opts["cookiefile"] = "cookies.txt"
    print("✅ cookies.txt 로드됨")
else:
    print("⚠ cookies.txt 없음 (일부 영상 재생 실패 가능)")

ffmpeg_opts = {
    "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
    "options": "-vn",
}

ytdl = youtube_dl.YoutubeDL(ytdl_opts)

class YTDLSource(nextcord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.title = data.get("title", "제목 없음")

    @classmethod
    async def from_url(cls, url, *, loop):
        data = await loop.run_in_executor(
            None, lambda: ytdl.extract_info(url, download=False)
        )

        if "entries" in data:
            data = data["entries"][0]

        return cls(
            nextcord.FFmpegPCMAudio(data["url"], **ffmpeg_opts),
            data=data
        )

# ===== Music Cog =====
class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.queue = []

    async def play_next(self, ctx):
        if self.queue:
            player = self.queue.pop(0)
            ctx.voice_client.play(
                player,
                after=lambda _: asyncio.run_coroutine_threadsafe(
                    self.play_next(ctx), self.bot.loop
                )
            )
            await ctx.send(f"🎵 재생중: **{player.title}**")
        else:
            await ctx.voice_client.disconnect()
            await ctx.send("📭 대기열 종료, 퇴장합니다")

    @commands.command()
    async def play(self, ctx, *, url):
        if not ctx.voice_client:
            if not ctx.author.voice:
                return await ctx.send("❌ 음성 채널에 먼저 들어가 주세요.")
            await ctx.author.voice.channel.connect()

        async with ctx.typing():
            try:
                player = await YTDLSource.from_url(url, loop=self.bot.loop)
            except Exception as e:
                return await ctx.send(f"❌ 음악 로드 실패:\n```{e}```")

        vc = ctx.voice_client
        if vc.is_playing():
            self.queue.append(player)
            await ctx.send(f"➕ 대기열 추가: **{player.title}**")
        else:
            vc.play(
                player,
                after=lambda _: asyncio.run_coroutine_threadsafe(
                    self.play_next(ctx), self.bot.loop
                )
            )
            await ctx.send(f"🎶 재생 시작: **{player.title}**")

bot.add_cog(Music(bot))

# ===== 실행 =====
token = os.environ.get("DISCORD_TOKEN")
if not token:
    raise RuntimeError("❌ DISCORD_TOKEN 환경변수가 없습니다")

bot.run(token)
