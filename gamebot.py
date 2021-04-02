from game import Game, Phase

import bot
import commands
import util

def admin_command(*, name, reinvoke=False):

    def wrapper(func):
        command = commands.command(name=name, reinvoke=reinvoke)(func)
        command.__command_checks__ = [lambda ctx: ctx.user.id in Game.ADMINS]
        return command

    return wrapper


def in_phase(*phases):

    def check(ctx):
        return Game.PHASE in phases

    return check


class GameBot(bot.Bot):

    @commands.command(name='signup', usage='名字')
    @commands.check(in_phase(Phase.PREPARING))
    def signup(self, ctx, name: str):
        """/signup 名字：专业"""
        self.add_user(ctx.user.id, name)
        ctx.reply('注册成功！ 请耐心等待游戏开始 ~ ')
        self.conn.send({'op': 'SYNC', 'd': None})

    @commands.command(name='start')
    @commands.check(in_phase(Phase.PREPARING))
    def start(self, ctx):
        ctx.reply('Halo ~ 请用 /signup 名字 进行注册！')

    @admin_command(name='broadcast', reinvoke=True)
    def broadcast(self, ctx, *args):
        message = '这是系统的提醒，不必回复：\n' + " ".join(args)
        for user in self.users:
            self.send_text(user.id, message)

    @admin_command(name='reload', reinvoke=True)
    def reload(self, ctx):
        ctx.reply("正在刷新玩家...")
        self._load_users()
        ctx.reply("刷新玩家成功！")
        self.invoke_command('dashboard', ctx)

    @admin_command(name='shuffle')
    def shuffle(self, ctx):
        ctx.reply("正在分配天使主人...")
        while True:
            shuffled = dict(zip(self.users, util.shuffled(self.users)))
            try:
                for sender, recipient in shuffled.items():
                    print(sender, recipient)
                    if sender == recipient:
                        raise StopIteration
                    sender.recipient = recipient
                    recipient.sender = sender
            except StopIteration:
                continue
            else:
                break
        self._save_users()
        ctx.reply("分配成功！ 记得用/reload")

    @commands.command(name="cat")
    @commands.check(in_phase(Phase.IN_PROGRESS))
    def cat(self, ctx):
        if self.__class__.__name__ == "Sender":
            self.send_photo(ctx.user.sender, 'cat.jpg')
        if self.__class__.__name__ == "Recipient":
            self.send_photo(ctx.user.recipient, 'cat.jpg')
        ctx.reply("He got cat ed!")

    @admin_command(name='dashboard')
    def dashboard(self, ctx):
        message = "GAMEPHASE: %s\nCurrent users: %s\n%s" % (
                Game.PHASE.value,
                len(self.users),
                "\n".join(["%s <-> %s" % (user, user.recipient) for user in self.users])
        )
        ctx.reply(message)

    @admin_command(name='gamephase', reinvoke=True)
    def gamephase(self, ctx, phase: str):
        Game.set_phase(phase)
        if Game.PHASE is Phase.IN_PROGRESS:
            self.invoke_command('broadcast', ctx, "天使与主人正式开始！ 大家跟主人/天使打个招呼 ~")
        if Game.PHASE is Phase.ENDING:
            self.invoke_command('broadcast', ctx, "天使与主任的活动要截止了哦 ~ 开始进入评分阶段, 大家请用 /rating 进行评分 ~ ")


class Sender(GameBot):

    @commands.command(name='/who')
    @commands.check(in_phase(Phase.ENDING))
    def who(self, ctx):
        ctx.reply("你的天使是: %s" % ctx.user.sender)


class Recipient(GameBot):

    @commands.command(name='/who')
    @commands.check(in_phase(Phase.IN_PROGRESS, Phase.ENDING))
    def who(self, ctx):
        ctx.reply("你的主人是: %s" % ctx.user.sender)

    @admin_command(name='gamephase', reinvoke=True)
    def gamephase(self, ctx, phase: str):
        Game.set_phase(phase)
        if Game.PHASE is Phase.IN_PROGRESS:
            for user in self.users:
                self.send_text(user.id, "你的主人是: %s" % user.recipient)
        if Game.PHASE is Phase.ENDING:
            self.invoke_command('broadcast', ctx, "天使与主任的活动要截止了哦 ~ 开始进入评分阶段, 大家请用 /rating 进行评分 ~ ")
