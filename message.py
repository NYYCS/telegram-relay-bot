import random
import os


class Message:

    def __init__(self, message=None, **attrs):
        if message:
            self.text = message.text
            self.photo = None
            if message.photo:
                self.photo = "%s.jpg" % random.randint(1000000, 9999999)
                message.photo[-1].get_file().download(self.photo)
            self.sticker = None
            if message.sticker:
                self.sticker = message.sticker.file_id
        else:
            self.text = attrs.pop('text', None)
            self.photo = attrs.pop('photo', None)
            self.sticker = attrs.pop('sticker', None)

    def send(self, user, *, bot):
        actual_bot = bot.updater.bot
        if self.text:
            actual_bot.send_message(user, self.text)
        if self.photo:
            with open(self.photo, 'rb') as photo:
                actual_bot.send_photo(user, photo)
            os.remove(self.photo)
        if self.sticker:
            actual_bot.send_sticker(user, self.sticker)

    def to_data(self):
        return dict(text=self.text, photo=self.photo, sticker=self.sticker)
