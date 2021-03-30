class Context:

    def __init__(self, bot, **attrs):
        self.bot = bot
        self.user = attrs.pop('user', None)
        if isinstance(self.user, int):
            self.user = self.bot.get_user(self.user)
        self.reinvoked_commands = attrs.pop('reinvoked_commands', set())

    def to_data(self):
        data = {
            'user': self.user.id,
            'reinvoked_commands': self.reinvoked_commands
        }
        return data

    def reply(self, text):
        if self.user:
            self.bot.send_text(self.user.id, text)
