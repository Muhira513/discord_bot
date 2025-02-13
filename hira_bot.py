import discord
from discord.ext import commands
import asyncio, youtube_dl
import yt_dlp as youtube_dl
import nextcord
from nextcord.ext import commands
from nextcord import Interaction, SlashOption, ChannelType
from nextcord.abc import GuildChannel

# 봇의 프리픽스 설정 (명령어 앞에 붙는 기호)
intents = discord.Intents.default()
intents.message_content = True  # 메시지 내용 접근 권한

bot = commands.Bot(command_prefix=commands.when_mentioned_or("!") and "!", intents=intents)

# 봇이 준비되었을 때 실행되는 이벤트
@bot.event
async def on_ready():
    print(f'로그인 성공! {bot.user} 님이 온라인 상태입니다.')
    await bot.change_presence(status=nextcord.Status.online, activity=nextcord.Game(name="디버그"))
        # 사용자 지정 상태 설정법
        # status=nextcord.Status.online      (온라인)
        # status=nextcord.Status.idle        (자리 비움)
        # status=nextcord.Status.dnd         (다른 용무)
        # status=nextcord.Status.offline     (오프라인)
        #
        #   ~~하는 중 등 상태 설정법
        # activity=nextcord.Game(name="하는 중")
        # activity=nextcord.Streaming(name="방송 중", url="올리고 싶은 URL")
        # activity=nextcord.Activity(type=nextcord.ActivityType.listening, name="듣는 중")
        # activity=nextcord.Activity(type=nextcord.ActivityType.watching, name="시청 중")

# 간단한 명령어 예시
                 
@bot.command()
async def 따라하기(ctx, *, text): ## 사용자 말 따라하는 봇
    await ctx.send(embed = discord.Embed(title= '따라하기', description= text, color = 0x00ff00))

@bot.command()
async def 들어와(ctx): ## 봇 음성채널 들어오게 하는 코드
    try: ##유저가 접속한 코드
        global vc
        vc = await ctx.message.author.voice.channel.connect()
    except:
        try:##유저가 접속하지 않으면 있는지 확인하는 코드
            await vc.move_to(ctx.message.author.voice.channel)
        except: ##유저가 없다고 출력하는 메시지 코드
            await ctx.send("채널에 유저가 접속하지 않았습니다.")    

@bot.command()
async def 나가(ctx):
    try:
        await vc.disconnect()
    except:
        await ctx.send("채널에 속해 있지 않습니다.")

@bot.command(aliases=['입장'])
async def join(ctx):
    if ctx.author.voice and ctx.author.voice.channel:
        channel = ctx.author.voice.channel      # 입장코드
        await channel.connect()
        print("음성 채널 정보: {0.author.voice}".format(ctx))
        print("음성 채널 이름: {0.author.voice.channel}".format(ctx))
    else:
        embed = nextcord.Embed(title='음성 채널에 유저가 존재하지 않습니다.',  color=nextcord.Color(0xFF0000))
        await ctx.send(embed=embed)
 
@bot.command(aliases=['퇴장'])
async def out(ctx):
    try:
        await ctx.voice_client.disconnect()   #퇴장 코드
    except AttributeError as not_found_channel:
        embed = nextcord.Embed(title='봇이 존재하는 채널을 찾지 못하였습니다.',  color=nextcord.Color(0xFF0000))
        await ctx.send(embed=embed)




youtube_dl.utils.bug_reports_message = lambda: ''



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
    'source_address': '0.0.0.0',  # bind to ipv4 since ipv6 addresses cause issues sometimes
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
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if 'entries' in data:
            # take first item from a playlist
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(nextcord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)



class Music(commands.Cog): #음악 재생을 위한 코드(클래스)
    def __init__(self, bot):
        self.bot = bot
        self.queue = []

    async def play_next(self, ctx):
        if self.queue:
            player = self.queue.pop(0)
            ctx.voice_client.play(player, after=lambda e: asyncio.run_coroutine_threadsafe(self.play_next(ctx), self.bot.loop))
            embed = nextcord.Embed(title=f'현재 재생중인 음악: {player.title}', color=nextcord.Color(0xF3F781))
            await ctx.send(embed=embed)
        else:
            await ctx.voice_client.disconnect()


    @commands.command(aliases=['노래'])
    async def play(self, ctx, *, url):
        async with ctx.typing():
            player = await YTDLSource.from_url(url, loop=self.bot.loop, stream=True)
            if ctx.voice_client is None:
                await ctx.author.voice.channel.connect()

            if not ctx.voice_client.is_playing():
                ctx.voice_client.play(player, after=lambda e: asyncio.run_coroutine_threadsafe(self.play_next(ctx), self.bot.loop))
                embed = nextcord.Embed(title=f'현재 재생중인 음악: {player.title}', color=nextcord.Color(0xF3F781))
                await ctx.send(embed=embed)
            else:
                self.queue.append(player)
                embed = nextcord.Embed(title=f'대기열에 추가됨: {player.title}', color=nextcord.Color(0x00ff00))
                await ctx.send(embed=embed)


    @commands.command(aliases=['볼륨'])
    async def volume(self, ctx, volume: int):


        if ctx.voice_client is None:
            embed = nextcord.Embed(title="음성 채널에 연결되지 않았습니다.",  color=nextcord.Color(0xFF0000))
            return await ctx.send(embed=embed)

        ctx.voice_client.source.volume = volume / 100  # 볼륨변경코드
        embed = nextcord.Embed(title=f"볼륨을 {volume}%으로 변경되었습니다.",  color=nextcord.Color(0x0040FF))
        await ctx.send(embed=embed)

    @commands.command(aliases=['삭제'])
    async def stop(self, ctx):

        await ctx.voice_client.disconnect()  # 음성채팅에서 나가는 코드

    @commands.command(aliases=['스킵'])
    async def skip(self, ctx):
        if ctx.voice_client.is_playing():
            ctx.voice_client.stop()
            embed = nextcord.Embed(title="다음 곡으로 건너뜁니다.", color=nextcord.Color(0x00ff00))
            await ctx.send(embed=embed)
        else:
            embed = nextcord.Embed(title="현재 재생 중인 곡이 없습니다.", color=nextcord.Color(0xFF0000))
            await ctx.send(embed=embed)

    @commands.command(aliases=['중지'])
    async def pause(self, ctx):


        if ctx.voice_client.is_paused() or not ctx.voice_client.is_playing():
            embed = nextcord.Embed(title="음악이 이미 일시 정지 중이거나 재생 중이지 않습니다.",  color=nextcord.Color(0xFF0000))
            await ctx.send(embed=embed)


        ctx.voice_client.pause()   # 정지하는 코드

    @commands.command(aliases=['재생'])
    async def resume(self, ctx):


        if ctx.voice_client.is_playing() or not ctx.voice_client.is_paused():   
            embed = nextcord.Embed(title="음악이 이미 재생 중이거나 재생할 음악이 존재하지 않습니다.",  color=nextcord.Color(0xFF0000))
            await ctx.send(embed=embed)

        ctx.voice_client.resume()    # 다시 재생하는 코드

    @play.before_invoke
    async def ensure_voice(self, ctx):
        if ctx.voice_client is None:
            if ctx.author.voice:
                await ctx.author.voice.channel.connect()
            else:
                embed = nextcord.Embed(title="음성 채널에 연결되어 있지 않습니다.",  color=nextcord.Color(0xFF0000))
                await ctx.send(embed=embed)
                raise commands.CommandError("작성자가 음성 채널에 연결되지 않았습니다.")
        elif ctx.voice_client.is_playing():
            ctx.voice_client.stop()

    @commands.command(aliases=['목록'])
    async def queue(self, ctx):
        if self.queue:
            queue_titles = '\n'.join(f'{idx + 1}. {song.title}' for idx, song in enumerate(self.queue))
            embed = nextcord.Embed(title='현재 대기열', description=queue_titles, color=nextcord.Color(0x00ff00))
        else:
            embed = nextcord.Embed(title='대기열이 비어 있습니다.', color=nextcord.Color(0xFF0000))
        await ctx.send(embed=embed)

    @commands.command(aliases=['추가'])
    async def add(self, ctx, *, url):
        async with ctx.typing():
            player = await YTDLSource.from_url(url, loop=self.bot.loop, stream=True)
            self.queue.append(player)
            embed = nextcord.Embed(title=f'대기열에 추가됨: {player.title}', color=nextcord.Color(0x00ff00))
            await ctx.send(embed=embed)

 
 
intents = nextcord.Intents.default()
intents.message_content = True





bot.add_cog(Music(bot))
# 봇 실행
bot.run('')  # 복사한 봇의 토큰을 여기에 넣으세요.