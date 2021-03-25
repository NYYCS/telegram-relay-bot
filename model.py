import random


class Context:

    def __init__(self, bot, user_id):
        self.bot = bot
        self.user_id = user_id
        self.stackcount = 0

    def send(self, text):
        self.bot.send_text(self.user_id, text=text)


class Message:

    def __init__(self, message):

        self.text = message.text
        self.photo = None
        self.sticker = None

        if message.photo:
            self.photo = "temp_%s.jpg" % random.randint(100000, 999999)
            message.photo[-1].get_file().download(self.photo)

        if message.sticker:
            self.sticker = message.sticker.file_id
