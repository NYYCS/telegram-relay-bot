from bot import User


class Context:

    def __init__(self, bot, **attrs):
        self.bot = bot
        self.user = attrs.pop('user', None)
        self.reinvoked_commands = attrs.pop('reinvoked_commands', set())

    def to_dict(self):
        d = {
            'user': self.user.id,
            'reinvoked_commands': self.reinvoked_commands
        }
        return d

    def reply(self, text):
        if self.user:
            self.bot.send_text(self.user.id, text)
