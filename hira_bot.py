import nextcord
from nextcord.ext import commands
import asyncio
import yt_dlp as youtube_dl
from nextcord import Interaction, SlashOption, ChannelType
from nextcord.abc import GuildChannel
import os

print(nextcord.opus.is_loaded())

# 봇의 프리픽스와 인텐트 설정
intents = nextcord.Intents.default()
intents.message_content = True 
intents.voice_states = True # 음성 채널 상태를 감지하기 위해 필요

bot = commands.Bot(command_prefix="!", intents=intents)

# 봇이 준비되었을 때 실행되는 이벤트
@bot.event
async def on_ready():
    print(f'로그인 성공! {bot.user} 님이 온라인 상태입니다.')
    await bot.change_presence(status=nextcord.Status.online, activity=nextcord.Game(name="디버그"))
    
    # 윈도우 터미널 인코딩 문제 해결 (한글 깨짐 방지)
    os.system("chcp 65001")

# 간단한 명령어 예시
@bot.command()
async def 따라하기(ctx, *, text): ## 사용자 말 따라하는 봇
    await ctx.send(embed = nextcord.Embed(title= '따라하기', description= text, color = 0x00ff00))

@bot.command(aliases=['입장'])
async def 들어와(ctx):
    if ctx.author.voice and ctx.author.voice.channel:
        channel = ctx.author.voice.channel
        try:
            await channel.connect()
            await ctx.send(f"**{channel.name}** 채널에 연결되었습니다.")
        except asyncio.TimeoutError:
            embed = nextcord.Embed(title='연결 시간 초과', description='음성 채널 연결에 실패했습니다. 네트워크 상태나 봇 권한을 확인해주세요.', color=nextcord.Color.red())
            await ctx.send(embed=embed)
    else:
        embed = nextcord.Embed(title='음성 채널에 유저가 존재하지 않습니다.', color=nextcord.Color.red())
        await ctx.send(embed=embed)

@bot.command(aliases=['나가', '퇴장'])
async def out(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("음성 채널에서 퇴장했습니다.")
    else:
        embed = nextcord.Embed(title='봇이 음성 채널에 연결되어 있지 않습니다.', color=nextcord.Color.red())
        await ctx.send(embed=embed)

# youtube_dl.utils.bug_reports_message = lambda: ''  <--- 이 줄을 삭제했습니다.

ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0',
}

ffmpeg_options = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn',
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

class YTDLSource(nextcord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        # yt-dlp의 정보 추출은 느릴 수 있으므로 executor에서 실행
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if 'entries' in data:
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(nextcord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.queue = []

    async def play_next(self, ctx):
        if self.queue:
            player = self.queue.pop(0)
            ctx.voice_client.play(player, after=lambda e: asyncio.run_coroutine_threadsafe(self.play_next(ctx), self.bot.loop))
            embed = nextcord.Embed(title=f'현재 재생중인 음악: {player.title}', color=nextcord.Color.yellow())
            await ctx.send(embed=embed)
        else:
            await asyncio.sleep(60) # 60초간 대기 후, 여전히 대기열이 비어있으면 퇴장
            if not self.queue and ctx.voice_client and not ctx.voice_client.is_playing():
                await ctx.voice_client.disconnect()
                await ctx.send("대기열이 비어있어 채널에서 나갑니다. 👋")

    @commands.command(aliases=['노래'])
    async def play(self, ctx, *, url):
        vc = ctx.voice_client
        if not vc:
            if not ctx.author.voice:
                await ctx.send("음성 채널에 먼저 연결해주세요.")
                return
            try:
                # 봇 연결 시도
                vc = await ctx.author.voice.channel.connect()
            except asyncio.TimeoutError:
                embed = nextcord.Embed(title='연결 시간 초과', description='음성 채널 연결에 실패했습니다. 네트워크 상태나 봇 권한을 확인해주세요.', color=nextcord.Color.red())
                await ctx.send(embed=embed)
                return

        # FFmpeg/yt-dlp를 사용하여 오디오 정보 추출
        async with ctx.typing():
            try:
                player = await YTDLSource.from_url(url, loop=self.bot.loop, stream=True)
            except Exception as e:
                embed = nextcord.Embed(title='음악 로드 실패', description=f'유튜브 정보를 가져오는 데 실패했습니다. 링크를 확인하거나 yt-dlp를 업데이트해주세요. (오류: {e})', color=nextcord.Color.red())
                await ctx.send(embed=embed)
                return


        if vc.is_playing() or vc.is_paused():
            self.queue.append(player)
            embed = nextcord.Embed(title=f'대기열에 추가됨: {player.title}', color=nextcord.Color.green())
            await ctx.send(embed=embed)
        else:
            vc.play(player, after=lambda e: asyncio.run_coroutine_threadsafe(self.play_next(ctx), self.bot.loop))
            embed = nextcord.Embed(title=f'현재 재생중인 음악: {player.title}', color=nextcord.Color.yellow())
            await ctx.send(embed=embed)

    @commands.command(aliases=['스킵'])
    async def skip(self, ctx):
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.stop()
            embed = nextcord.Embed(title="다음 곡으로 건너뜁니다. ⏩", color=nextcord.Color.green())
            await ctx.send(embed=embed)
        else:
            embed = nextcord.Embed(title="현재 재생 중인 곡이 없습니다. 🤷‍♂️", color=nextcord.Color.red())
            await ctx.send(embed=embed)

    @commands.command(aliases=['중지'])
    async def pause(self, ctx):
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.pause()
            embed = nextcord.Embed(title="음악을 일시 정지합니다. ⏸️", color=nextcord.Color.yellow())
            await ctx.send(embed=embed)
        else:
            embed = nextcord.Embed(title="재생 중인 음악이 없어 일시 정지할 수 없습니다. ⛔", color=nextcord.Color.red())
            await ctx.send(embed=embed)

    @commands.command(aliases=['재생'])
    async def resume(self, ctx):
        if ctx.voice_client and ctx.voice_client.is_paused():
            ctx.voice_client.resume()
            embed = nextcord.Embed(title="음악을 다시 재생합니다. ▶️", color=nextcord.Color.green())
            await ctx.send(embed=embed)
        else:
            embed = nextcord.Embed(title="일시 정지된 음악이 없습니다. 🤷‍♂️", color=nextcord.Color.red())
            await ctx.send(embed=embed)

    @commands.command(aliases=['목록'])
    async def queue(self, ctx):
        if self.queue:
            queue_titles = '\n'.join(f'{idx + 1}. {song.title}' for idx, song in enumerate(self.queue))
            embed = nextcord.Embed(title='🎵 현재 대기열', description=queue_titles, color=nextcord.Color.blue())
        else:
            embed = nextcord.Embed(title='대기열이 비어 있습니다. 텅~', color=nextcord.Color.red())
        await ctx.send(embed=embed)

bot.add_cog(Music(bot))

# 봇 실행
bot.run('')
