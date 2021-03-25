from telegram.ext import Updater, MessageHandler, Filters
from threading import Thread

from game import CURRENT_GAME_STATE
from model import Context, Message
from util import *

import inspect
import os

def command(*, name):
    def wrapper(func):
        func.__command__ = '/' + name
        return func

    return wrapper

class BotMeta(type):

    def __new__(mcs, *args, **kwargs):

        cls = super().__new__(mcs, *args, **kwargs)

        commands = {}

        for base in reversed(cls.__mro__):
            for attr, value in base.__dict__.items():
                if not attr.startswith("__"):
                    try:
                        command = value.__command__
                    except AttributeError:
                        continue
                    commands[command] = value

        cls.__commands__ = commands

        return cls


class Bot(metaclass=BotMeta):

    def __new__(cls, *args, **kwargs):
        self = super().__new__(cls)
        self._commands = cls.__commands__
        return self

    def __init__(self, token, conn):
        self.updater = Updater(token, use_context=True)
        self._bot = self.updater.bot
        self.updater.dispatcher.add_handler(MessageHandler(Filters.command, self.listen_for_commands))
        self.updater.dispatcher.add_handler(MessageHandler(Filters.all & (~Filters.command), self.listen_for_message))
        self.signal_listener = Thread(target=self.listen_for_signal, daemon=True)
        self.conn = conn

        self.listeners = []

        if CURRENT_GAME_STATE == 'START':
            self._recipients = load_yaml(self.botname)

    @property
    def botname(self):
        return self.__class__.__name__.lower()

    @property
    def members(self):
        return list(self._recipients.keys())

    def signal_call(self, command_name, ctx, *args):
        ctx.stackcount += 1
        payload = {
            'name': command_name,
            'args': args
        }
        self.conn.send(payload)

    def listen_for_commands(self, update, ctx):
        raw_text = update.message.text
        command_name, *args = raw_text.split(" ")
        try:
            ctx = Context(self, update.effective_user.id)
            self.invoke_command(command_name, ctx, *args)
        except Exception:
            import traceback
            traceback.print_exc()
            update.message.reply_text("命令用法错误！")

    def invoke_command(self, command_name, *args):

        ctx, *args = args

        if ctx.stackcount <= 1:

            try:
                command = self._commands[command_name]
            except KeyError:
                pass
            else:

                argnames, varargs, *_, annotations = inspect.getfullargspec(command)

                if varargs:
                    command(ctx, *args)
                else:
                    # Trim extra arguments
                    args = args[:len(argnames)]

                    cleaned_args = []

                    for argname, arg in zip(argnames, args):
                        if argname in annotations:
                            cls = annotations[argname]
                            arg = cls(arg)
                        cleaned_args.append(arg)

                    command(ctx, *cleaned_args)



    def listen_for_message(self, update, ctx):
        user, message = update.effective_user, update.message
        if user.id in self.members:

            if self.listeners:
                for i, listener in enumerate(self.listeners):
                    listener.send(message)

            recipient = self._recipients[user.id]

            self.signal_call('send_message', recipient, Message(message))

    def listen_for_signal(self):
        while True:
            payload = self.conn.recv()
            ctx, *args = payload['args']
            func = getattr(self, payload['name'])
            func(*args)

    def send_message(self, user_id, message):
        for attr in ('text', 'photo', 'sticker'):
            if getattr(message, attr, None):
                send = getattr(self, "send_" + attr)
                return send(user_id, message=message)

    def send_text(self, chat_id, *, text=None, message=None):
        if text:
            self._bot.send_message(chat_id, text)
        else:
            self._bot.send_message(chat_id, message.text)

    def send_sticker(self, chat_id, *, file_id=None, message=None):
        s = file_id or message.sticker
        self._bot.send_sticker(chat_id, s)

    def send_photo(self, chat_id, *, path=None, message=None):
        if message:
            with open(message.photo, 'rb') as f:
                self._bot.send_photo(chat_id, f)
            os.remove(message.photo)
        else:
            with open(path, 'rb') as f:
                self._bot.send_photo(chat_id, f)