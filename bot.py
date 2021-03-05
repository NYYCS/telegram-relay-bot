from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from contextlib import contextmanager
from ruamel.yaml import YAML
from threading import Thread, Lock
import random

yaml = YAML()

from handlers import *

class BotException(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(message)

class CommandUsageError(BotException):
    def __init__(self, *, usage=None):
        message = "错误使用command！{0}".format('' if usage is None else '\n' + usage)
        super().__init__(message)


@contextmanager
def update_yaml(filename):
    data = load_yaml(filename)
    yield data
    save_yaml(filename, data)

def load_yaml(filename):
    try:
        with open(filename, 'rb') as f:
            return yaml.load(f)
    except:
        return {}

def save_yaml(filename, data):
    with open(filename, 'wb') as f:
        yaml.dump(data, f)

# GAME CONSTANTS
GAME = load_yaml('game.yaml')
STATUS = GAME['status']
ADMINS = GAME['admins']


def is_admin(send=True):

    def wrapper(func):
        def wrapped(self, update, ctx):
            if update.effective_user.id in ADMINS:
                if send:
                    self.send_admin_command(func)
                return func(self, update, ctx)
        return wrapped
    return wrapper


class Bot:

    def __init__(self, token, r_pipe, a_pipe):
        self.updater = Updater(token, use_context=True)
        self.dispatcher = self.updater.dispatcher
        self._queue = self.updater.job_queue
        self.bot = self.updater.bot
        self.status = None

        self.lock = Lock()

        self._send_to = load_yaml(self.name + '.yaml')
        self._relay_pipe = r_pipe
        self._admin_pipe = a_pipe
        self._relay_thread = Thread(target=self.relay_message, daemon=True)
        self._admin_thread = Thread(target=self.recv_admin_command, daemon=True)

        # self.dispatcher.add_error_handler(self.error_handler)

        self.dispatcher.add_handler(CommandHandler('start', self.start_command))
        self.dispatcher.add_handler(CommandHandler('signup', self.signup_command))
        self.dispatcher.add_handler(CommandHandler('rate', self.rate_command))
        self.dispatcher.add_handler(CommandHandler('broadcast', self.broadcast_command))
        self.dispatcher.add_handler(CommandHandler('game_start', self.game_start_command))
        self.dispatcher.add_handler(CommandHandler('shuffle', self.setup_users_command))

        self.dispatcher.add_handler(MessageHandler(Filters.all & (~Filters.command), self.recv_message))

    def start_command(self, update, ctx):
        update.message.reply_text('请用 /signup <your_name> 进行注册!')

    def signup_command(self, update, ctx):
        try:
            user_id, name = update.effective_user.id, ctx.args[0]
        except IndexError:
            raise CommandUsageError(usage='/signup <your_name>')
        entry = {
            'name': name,
            'score': {
                'tianshi': 0,
                'zhuren': 0
            },
            'rating': {
                'tianshi': 0,
                'zhuren': 0
            }
        }
        with update_yaml('users.yaml') as users:
            users[user_id] = entry
        update.message.reply_text('注册成功！ 请等待游戏开始 ~')

    def rate_command(self, update, ctx):
        if self.status == 2:
            try:
                rating = int(ctx.args[0])
            except (IndexError, ValueError):
                raise CommandUsageError(usage='/rating <your_rating> 分数 <= 25')

            if rating >= 25 or rating < 0:
                raise CommandUsageError(usage='/rating <your_rating> 分数 <= 25')
            user = update.effective_user.id
            self.add_rating(self._send_to[user.id], rating)

    def setup_users(self):
        users = load_yaml('users.yaml')
        while True:
            pairs = {}
            a, b = list(users.copy().keys()), list(users.copy().keys())
            random.shuffle(a)
            random.shuffle(b)
            for x, y in zip(a, b):
                if x == y:
                    pass
                pairs[x] = y
            break
        save_yaml('tianshi.yaml', pairs)
        save_yaml('zhuren.yaml', {
            v: k for k, v in pairs.items()
        })

    def game_start(self):
        with update_yaml('game.yaml') as game:
            self.status = game['status'] = 1
        self._send_to = load_yaml(self.__class__.__name__.lower() + '.yaml')
        self.broadcast('GAME START')
        print(self._send_to)

    def broadcast(self, text):
        for user_id in self.players:
            self.bot.send_message(user_id, text)

    @is_admin(send=False)
    def setup_users_command(self, update, ctx):
        self.setup_users()

    @is_admin()
    def game_start_command(self, update, ctx):
        self.game_start()

    @is_admin(send=False)
    def broadcast_command(self, update, ctx):
        text = "[SYSTEM]" + " ".join(ctx.args)
        self.broadcast(text)

    def send_admin_command(self, func, arg):
        self._admin_pipe.send(func.__name__[:-8], arg)

    def recv_admin_command(self):
        funcname = self._admin_pipe.recv()
        func = getattr(self, funcname)
        func()

    def recv_message(self, update, ctx):
        if self.status == 0:
            raise BotException('游戏还没开始 ~')
        if self.status == 2:
            raise BotException('游戏结束了 ~')
        user, message = update.effective_user, update.message
        if user.id in self.players:
            message_type, handler = get_recv_handler(message)
            if handler is not None:
                payload = {
                    'user_id': self._send_to[user.id],
                    'type': message_type,
                    'arg': handler(message),
                }
                self._relay_pipe.send(payload)
                self.add_score(user.id)

    def relay_message(self):
        while True:
            payload = self._relay_pipe.recv()
            handler = get_send_handler(payload)
            self._queue.run_once(handler, 0.1)

    def add_score(self, user_id):
        with self.lock:
            with update_yaml('users.yaml') as users:
                users[user_id]['score'][self.name] += 1

    def add_rating(self, user_id, score):
        with update_yaml('users.yaml') as users:
            users[user_id]['rating'][self.name] = score

    @classmethod
    def run(cls, token, r_pipe, a_pipe):
        self = cls(token, r_pipe, a_pipe)
        self._admin_thread.start()
        self._relay_thread.start()
        self.updater.start_polling()

        print(self.name, "RUNNING...")

    @property
    def name(self):
        return self.__class__.__name__.lower()

    @property
    def players(self):
        return list(self._send_to.keys())

    def error_handler(self, update, ctx):
        message = ctx.error.message if getattr(ctx.error, 'message', None) else ' '.join(ctx.error.args)
        update.message.reply_text(message)

class Tianshi(Bot):
    pass

class Zhuren(Bot):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.dispatcher.add_handler(CommandHandler('who', self.who_command))

    def game_start(self):
        super().game_start()
        users = load_yaml('users.yaml')
        for a_id, z_id in self._send_to.items():
            self.bot.send_message(a_id, '你的主人是: %s' % users[z_id]['name'])

    def who_command(self, update, ctx):
        a_id = update.effective_user.id
        users = load_yaml('users.yaml')
        z_id = self._send_to[a_id]
        self.bot.send_message(a_id, '你的主人是: %s' % users[z_id]['name'])