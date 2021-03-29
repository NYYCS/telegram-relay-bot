
import commands
import util
import bot

from game import Game, Phase


def admin_command(*, name, reinvoke=False):

    def wrapper(func):
        command = commands.command(name=name, reinvoke=reinvoke)(func)
        command.__command_checks__ = [lambda ctx: ctx.user.id in Game.ADMINS]
        return command

    return wrapper

def in_phase(phase):

    def check(ctx):
        return Game.PHASE is phase

    return check


class GameBot(bot.Bot):

    @commands.command(name='signup')
    @commands.check(in_phase(Phase.PREPARING))
    def signup(self, ctx, name: str):
        self.add_user(ctx.user.id, name)
        ctx.reply('注册成功！ 请耐心等待游戏开始 ~ ')

    @commands.command(name='start')
    @commands.check(in_phase(Phase.PREPARING))
    def start(self, ctx):
        ctx.reply('Halo ~ 请用`/signup 名字`进行注册！')

    @commands.command(name='rating')
    @commands.check(in_phase(Phase.ENDING))
    def rating(self, ctx, num):
        pass

    @admin_command(name='broadcast', reinvoke=True)
    def broadcast(self, ctx, *args):
        message = '这是系统的提醒，不必回复：\n' + " ".join(args)
        for user in self.users:
            self.send_text(user.id, message)

    @admin_command(name='reload', reinvoke=True)
    def reload(self, ctx):
        pass


    @admin_command(name='shuffle')
    def shuffle(self, ctx):
        ctx.reply("正在分配天使主人...")
        while True:
            shuffled = dict(zip(self.users, util.shuffled(self.users)))
            try:
                for sender, recipient in shuffled.items():
                    if sender == recipient or shuffled[recipient] == sender:
                        raise StopIteration
            except StopIteration:
                continue
            else:
                break



    @admin_command(name='dashboard')
    def dashboard(self, ctx):
        message = "Current users: %s\n" % len(self.users) + "\n".join(self.users)
        ctx.reply(message)

    @admin_command(name='gamephase', reinvoke=True)
    def gamephase(self, ctx, phase: str):
        Game.set_phase(phase)
        if Game.PHASE is Phase.IN_PROGRESS:
            self.invoke_command('broadcast', ctx, "天使与主人正式开始！ 大家跟主人/天使打个招呼 ~")
        if Game.PHASE is Phase.ENDING:
            self.invoke_command('broadcast', ctx, "天使与主任的活动要截止了哦 ~ 开始进入评分阶段, 大家请用`/rating`进行评分 ~ ")

class Angel(GameBot):

    @commands.command(name='/who')
    @commands.check(in_phase(Phase.ENDING))
    def who(self, ctx):
        ctx.reply("你的天使是: %s" % ctx.user.sender)

class Dumbs(GameBot):   # TODO Change name

    @commands.command(name='/who')
    @commands.check(in_phase(Phase.ENDING))
    def who(self, ctx):
        ctx.reply("你的天使是: %s" % ctx.user.sender)

    @admin_command(name='gamephase', reinvoke=True)
    def gamephase(self, ctx, phase: str):
        Game.set_phase(phase)
        if Game.PHASE is Phase.IN_PROGRESS:
            self.invoke_command('broadcast', ctx, "天使与主人正式开始！ 大家跟主人/天使打个招呼 ~")
            for user in self.users:
                self.send_text(user.id, "你的主人是: %s" % ctx.user.recipient)
        if Game.PHASE is Phase.ENDING:
            self.invoke_command('broadcast', ctx, "天使与主任的活动要截止了哦 ~ 开始进入评分阶段, 大家请用`/rating`进行评分 ~ ")





