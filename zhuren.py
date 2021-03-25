from bot import command
from game import USERS
from model import Context, Message

from tianshi import Tianshi

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