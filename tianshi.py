from bot import Bot, command
from game import GAME, CURRENT_GAME_STATE, ADMINS, USERS
from util import *

import random


def is_game_state(*, state):
    def wrapped(func):
        def wrapper(*args, **kwargs):
            if CURRENT_GAME_STATE in state:
                return func(*args, **kwargs)

        return wrapper

    return wrapped


def is_admin(func):
    def wrapped(self, ctx, *args):
        if ctx.user_id in ADMINS:
            return func(self, ctx, *args)

    return wrapped


class Tianshi(Bot):

    @command(name='signup')
    @is_game_state(state=['PRE'])
    def signup(self, ctx, name: str):
        USERS[ctx.user_id] = {
            'name': name,
            'rating': {
                'tianshi': [],
                'zhuren': []
            }
        }
        save_yaml('users', USERS)
        self.send_text(ctx.user_id, text='注册成功！ 请耐性等待游戏开始 ~')

    @command(name='shuffle')
    @is_admin
    def shuffle(self, ctx):
        users = load_yaml('users')

        self.send_text(ctx.user_id, text="Shuffling...")
        while True:
            try:
                shuffled = {}
                a, b = list(users.copy().keys()), list(users.copy().keys())

                random.shuffle(a)
                random.shuffle(b)
                for x, y in zip(a, b):
                    if a == b:
                        raise Exception
                    shuffled[x] = y

                for x, y in shuffled.items():
                    if shuffled[y] == x:
                        raise Exception
            except:
                continue
            else:
                break

        self.send_text(ctx.user_id, text="Done shuffling. %s pairs" % len(shuffled))
        inverted = {
            v: k for k, v in shuffled.items()
        }
        save_yaml('tianshi', shuffled)
        save_yaml('zhuren', inverted)
        print("\n".join(["%s <=> %s" % (k, v) for k, v in shuffled.items()]))
        self.send_text(ctx.user_id, text="\n".join(["%s <=> %s" % (k, v) for k, v in shuffled.items()]))

    @command(name='cgs')
    @is_admin
    def cgs(self, ctx, state):
        CURRENT_GAME_STATE = GAME['game_state'] = state
        save_yaml('game', GAME)
        if CURRENT_GAME_STATE == 'START':
            self.on_start(ctx, state)
        self.signal_call('invoke_command', '/cgs', ctx, state)

    def on_start(self, ctx, state):
        self.invoke_command('/reload', ctx)
        self.invoke_command('/b', ctx, '游戏开始！ 你们可以开始聊天了！')

    @command(name='b')
    @is_admin
    def b(self, ctx, *args):
        prefix = '这是系统的提醒，不必回复：\n'
        text = ' '.join(args)
        for member_id in self.members:
            self.send_text(member_id, text=prefix + text)
        self.signal_call('invoke_command', '/b', ctx, *args)

    @command(name='stats')
    @is_admin
    def stats(self, ctx):
        text = '现共有%s个人参与:\n%s' % (len(USERS), "\n".join("%s <=> %s" % (k, v) for k, v in self._recipients.items()))
        self.send_text(ctx.user_id, text=text)

    @command(name='reload')
    @is_admin
    def reload(self, ctx):
        self.send_text(ctx.user_id, text='Reloading...')
        self._recipients = load_yaml(self.botname)
        self.send_text(ctx.user_id, text='Done Reloading...')
        self.invoke_command('/stats', ctx)
        self.signal_call('invoke_command', '/reload', ctx)

    @classmethod
    def run(cls, token, conn):
        self = cls(token, conn)
        self.updater.start_polling()
        self.signal_listener.start()
        print(self.botname, "ready to go...")


class Zhuren(Tianshi):

    def on_start(self, ctx, state):
        super().on_start(ctx, state)
        for member in self.members:
            name = USERS[ctx.user_id]['name']
            self.send_text(member, text="你的主人是: %s" % name)

    @command(name='who')
    def who(self, ctx):
        name = USERS[ctx.user_id]['name']
        self.send_text(ctx.user_id, text="你的主人是: %s" % name)
