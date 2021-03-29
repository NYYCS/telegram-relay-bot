import inspect
import random

from collections import namedtuple
from telegram.ext import Updater, MessageHandler, Filters

from context import Context
from commands import Command
from exception import CommandUsageError


import util



class User:

    def __init__(self, id, name):
        self.id = id
        self.name = name

    def __hash__(self):
        return self.id

    def __eq__(self, other):
        return self.id == other.id and isinstance(other, self.__class__)

    def __str__(self):
        return self.name



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
        return self

    def __init__(self, token, conn):
        self.updater = Updater(token)
        self.updater.dispatcher.add_handler(
            MessageHandler(Filters.command, self.command_listener)
        )

        self.conn = conn

        self._users = {}

    def add_user(self, id, name):
        pass

    def get_user(self, id):
        return self._users[id] if id in self._users else User(id, 'Dummy')

    def get_context(self, *, update=None, data=None, cls=Context):
        if update:
            user = self.get_user(update.effective_user)
            return cls(self, user=user)
        if data:
            return cls(self, **data)

    def send_command(self, ctx, command, *args):
        ctx.reinvoked_commands.add(command)
        payload = {
            'op': 'COMMAND',
            'd' : {
                'command': command,
                'context': ctx.to_dict(),
                'arguments': args
            }
        }
        self.conn.send(payload)

    def _listener(self):
        while True:

            payload = self.conn.recv()
            opcode, data = payload['op'], payload['d']

            if opcode == 'COMMAND':
                command = data['command']
                ctx = self.get_context(**data['ctx'])
                args = data['args']
                return self.invoke_command(command, ctx, *args)


    def command_listener(self, update, ctx):
        command_name, *args = update.message.text.split(" ")
        ctx = self.get_context(update=update)
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
                ctx.send(e)
            else:
                ctx.send('Bot有问题，err跟负责人讲一下')  # TODO Error

