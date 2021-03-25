import inspect
import random
import os

import multiprocessing

from collections import namedtuple

User = namedtuple('User', 'id name')

def command(*, name, checks=None, send=False):
    def wrapper(func):
        func.__command_attrs__ = {
            'name': name,
            'checks': checks,
            'send': send
        }
        return func
    return wrapper

class CommandUsageError(Exception):

    def __init__(self, command):
        self.message = message = '命令用法错误！\n`%s`' % command.usage
        super().__init__(message)

class Command:

    def __init__(self, callback, name, *, checks=None, send=False):
        self.callback = callback
        self.name = name
        self.prefixed_name = "/" + self.name
        self.send = send

        argnames, varargs, *_, annotations = inspect.getfullargspec(self.callback)

        self._varargs = varargs

        if self._varargs:
            self.usage = "`%s message`" % self.prefixed_name
        else:
            self.usage = "`%s %s" % (self.prefixed_name, " ".join(argnames))
            self.converters = [
                annotations[argname] if argname in annotations
                else None for argname in annotations
            ]

        self.checks = checks if checks else []

    def __str__(self):
        return '%s command' % self.prefixed_name

    def invoke(self, bot, ctx, *args):
        for check in self.checks:
            if not check(ctx):
                raise Exception

        if self._varargs:
            self.callback(bot, ctx, *args)
        else:
            cleaned = []
            for arg, converter in zip(args, self.converters):
                if converter is not None:
                    arg = converter(arg)
                cleaned.append(arg)
            self.callback(bot, ctx, *cleaned)

        if self.send:
            bot.send_command(self.prefixed_name, ctx, *args)

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

class Message:

    def __init__(self, message):
        self.text = message.text
        self.photo = None
        if message.photo:
            filename = "%s_.jpg" % random.randint(1000000, 9999999)
            message.photo[-1].get_file().download(filename)
            self.photo = filename
        self.sticker = None
        if message.sticker:
            self.sticker = message.sticker.file_id

class BotMeta(type):

    def __new__(mcs, *args, **kwargs):
        cls = super().__new__(mcs, *args, **kwargs)

        commands = {}

        for base in reversed(cls.__mro__):
            for attr, value in base.__dict__.items():
                if not attr.startswith("__"):
                    try:
                        command_attrs = value.__command_attrs__
                    except AttributeError:
                        continue
                    command = Command(value, **command_attrs)
                    commands[command.name] = command

        cls.__commands__ = commands

        return cls

class Bot(metaclass=BotMeta):

    def __new__(cls, *args, **kwargs):
        self = super().__new__(cls)
        self.commands = cls.__commands__

    def __init__(self, token, conn):
        self.token = token
        self.bot = None
        self.conn = conn

    def get_context(self, update=None, *, data=None):
        if data is not None:
            return Context.from_data(self, data)
        else:
            return Context(self, update)

    def command_listener(self, update, ctx):
        command_name, *args = update.message.text.split(" ")
        ctx = self.get_context(update)
        try:
            self.invoke_command(command_name.lstrip('/'), ctx, *args)
        except KeyError:
            pass

    def invoke_command(self, command, ctx, *args):
        if isinstance(command, str):
            command = self.commands[command]
        try:
            command.invoke(self, ctx, *args)
        except Exception as e:
            if isinstance(e, CommandUsageError):
                ctx.send(e.message)
            else:
                ctx.send('Bot有问题，err跟负责人讲一下') #TODO Error









