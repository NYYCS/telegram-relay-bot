
class Context:

    def __init__(self, bot, update=None):
        self.bot = bot
        if update:
            data = {
                'user': self.bot.get_user(update.effective_user.id),
            }
            self._from_data(data)

    def _from_data(self, data):
        self.user = data.pop('user')

    def send(self, text):
        self.bot.send_text(self.user.id, text)

    @classmethod
    def from_data(cls, bot, data):
        ctx = cls(bot)
        ctx._from_data(data)
        return ctx