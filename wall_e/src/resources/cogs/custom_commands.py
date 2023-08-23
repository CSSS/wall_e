import random

from discord.ext import commands


class CustomCommands(commands.Cog):

    def __init__(self, bot, config, bot_loop_manager):
        pass

    @commands.command()
    async def cmpt276(self, ctx):
        await ctx.send("NOT LIKE THIS NAZ, NOT LIKE THIS")

    @commands.command()
    async def cmpt361(self, ctx):
        await ctx.send("CAN'T HELP YOU TOO DAMN HARD")

    @commands.command()
    async def cmpt376(self, ctx):
        await ctx.send("HOW DARE YOU CALL UPON ME, REWRITE THAT COMMAND FILTHY PEASANT")

    @commands.command()
    async def f(self, ctx):
        await ctx.send("<:F_Eggplant:313248902021120000> <:F_Eggplant:313248902021120000> "
                       "<:F_Eggplant:313248902021120000> <:F_Eggplant:313248902021120000>\n"
                       "<:F_Eggplant:313248902021120000>\n<:F_Eggplant:313248902021120000> "
                       "<:F_Eggplant:313248902021120000> <:F_Eggplant:313248902021120000>\n"
                       "<:F_Eggplant:313248902021120000>\n<:F_Eggplant:313248902021120000>"
                       )

    @commands.command()
    async def gnu(self, ctx):
        await ctx.send(
            "```I'd just like to interject for moment. What you're refering to as Linux, is in fact, GNU/Linux, or "
            "as I've recently taken to calling it, GNU plus Linux. Linux is not an operating system unto itself, but "
            "rather another free component of a fully functioning GNU system made useful by the GNU corelibs, shell "
            "utilities and vital system components comprising a full OS as defined by POSIX.\n\nMany computer users "
            "run a modified version of the GNU system every day, without realizing it. Through a peculiar turn of "
            "events, the version of GNU which is widely used today is often called Linux, and many of its users are "
            "not aware that it is basically the GNU system, developed by the GNU Project. \n\nThere really is a "
            "Linux, and these people are using it, but it is just a part of the system they use. Linux is the "
            "kernel: the program in the system that allocates the machine's resources to the other programs that "
            "you run. The kernel is an essential part of an operating system, but useless by itself; it can only "
            "function in the context of a complete operating system. Linux is normally used in combination with the "
            "GNU operating system: the whole system is basically GNU with Linux added, or GNU/Linux. All the "
            "so-called Linux distributions are really distributions of GNU/Linux!```"
        )

    @commands.command()
    async def impeach(self, ctx):
        await ctx.send(
            "https://theawesomedaily.com/wp-content/uploads/2018/06/you-have-no-power-here-meme-feat-good-1.jpg")

    @commands.command()
    async def macm101(self, ctx):
        await ctx.send("Easy GPA booster, ~~study hard~~ no studying needed.")

    @commands.command()
    async def macm316(self, ctx):
        await ctx.send("TEARS OF SALT")

    @commands.command()
    async def math150(self, ctx):
        await ctx.send("like 151 but on steroids")

    @commands.command()
    async def math152(self, ctx):
        await ctx.send("makes you wish you failed calc 1")

    @commands.command()
    async def medipack(self, ctx):
        await ctx.send("WHO IS HE?!?!?!?")

    @commands.command()
    async def monty(self, ctx):
        await ctx.send(
            "RIP Monty Oum.\n`\"I believe that the human spirit is indomitable. If you endeavor to achieve, it will "
            "happen given enough resolve. It may not be immediate, and often your greater dreams is something you "
            "will not achieve within your own lifetime. The effort you put forth to anything transcends yourself, "
            "for there is no futility even in death.\"`"
        )

    @commands.command()
    async def prettygood(self, ctx):
        await ctx.send("https://pm1.narvii.com/6455/cfc754b99032891e8fce5ef346ddd96c828bf6be_hq.jpg")

    @commands.command()
    async def psyduck(self, ctx):
        num = random.randint(0, 2)
        if num == 0:
            await ctx.send("https://media.giphy.com/media/fxIiymxLITF0QMZXWH/giphy.gif")
        elif num == 1:
            await ctx.send("https://media.giphy.com/media/xTv6kG7GUXfj2/giphy.gif ")
        elif num == 2:
            await ctx.send("https://tenor.com/view/pokemon-trip-nintendo-psy-duck-camera-gif-5709088")

    @commands.command()
    async def thebest(self, ctx):
        await ctx.send("404: Best not found.")
