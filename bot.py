import telegram.ext as tg

from threading import Thread, Lock
import random
from ruamel.yaml import YAML
import ruamel.yaml
import json
import os

yaml = YAML()

with open('members.yaml', 'r') as f:
    MEMBERS = yaml.load(f)

LOCK = Lock()

class Bot:

    def __init__(self, token, pipe, targets):
        self.updater = tg.Updater(token=token, use_context=True)
        self.dispatcher = self.updater.dispatcher
        self.job_queue = self.updater.job_queue

        self._scores = {}

        self._pipe = pipe
        self._loop = Thread(target=self._internal_loop, daemon=True)

        self.targets = targets

        self.dispatcher.add_handler(tg.MessageHandler(tg.Filters.all, self.on_message))
        self.dispatcher.add_handler(tg.CommandHandler('start', self.start))

        self.job_queue.run_repeating(self._record_score, 60)

    def _record_score(self, ctx):
        print("SAVING SCORES...")
        with LOCK:
            with open(self.__class__.__name__.lower() + "_score.json", 'r') as f:
                scores = json.load(f)
                for user_id, to_add in self._scores.items():
                    scores[str(user_id)] += to_add
            with open(self.__class__.__name__.lower() + "_score.json", 'w') as f:
                json.dump(scores, f)
                self._scores = {}

    def on_message(self, update, ctx):

        user = update.effective_user

        if user.id in MEMBERS:

            message = update.message
            payload = {
                'user_id': self.targets[user.id]
            }

            if message.text:
                payload['type'] = 'text'
                payload['data'] = message.text

            if message.sticker:
                payload['type'] = 'sticker'
                payload['data'] = message.sticker.file_id

            if message.photo:
                payload['type'] = 'photo'
                path = str(random.randint(100000, 999999)) + "_temp.jpg"
                message.photo[-1].get_file().download(path)
                payload['data'] = path

            if payload.get('type') is not None:
                self._pipe.send(payload)
                if user.id not in self._scores:
                    self._scores[user.id] = 0
                self._scores[user.id] += 1

        else:

            ctx.bot.send_message(user.id, "你不是玩家！")

    def start(self, update, ctx):
        user = update.effective_user
        with LOCK:
            with open('members.yaml', 'r+') as f:
                members = yaml.load(f)
                members[user.id] = "%s %s" % (user.first_name, user.last_name)
                yaml.dump(members, f)

    def _internal_loop(self):

        while True:

            payload = self._pipe.recv()

            def send_message(ctx):

                def _send_photo(chat_id, filename):
                    with open(filename, 'rb') as f:
                        ctx.bot.send_photo(chat_id, f)
                    os.remove(filename)

                funcs = {
                    'text': ctx.bot.send_message,
                    'photo': _send_photo,
                    'sticker': ctx .bot.send_sticker
                }

                func = funcs.get(payload['type'])
                func(payload['user_id'], payload['data'])

            self.job_queue.run_once(send_message, 0.2)

    @classmethod
    def run(cls, token, pipe, targets):
        self = cls(token, pipe, targets)
        self._loop.start()
        self.updater.start_polling()
        print("WAITING FOR MESSAGES...")

class Angel(Bot):
    pass

class Host(Angel):

    def who(self, update, ctx):
        user = update.effective_user
        try:
            host_id = self.targets[user.id]
            name = MEMBERS[host_id]
        except KeyError:
            ctx.bot.send_message(chat_id=user.id, text="你不是玩家！")
        else:
            ctx.bot.send_message(chat_id=user.id, text="你的主人是: %s" % name)
