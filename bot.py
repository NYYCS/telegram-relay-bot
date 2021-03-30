from telegram.ext import Updater, MessageHandler, Filters

from threading import Thread

from commands import Command, CommandError
from message import Message
from context import Context
from game import Game, Phase
from user import User

import util


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
        self.updater.dispatcher.add_handler(
            MessageHandler(Filters.all & (~Filters.command), self.message_listener)
        )

        self.conn = conn

        self._load_users()

    @property
    def users(self):
        return list(self._users.values())

    def add_user(self, id, name):
        self._users[id] = User(self, id, name=name)
        self._save_users()

    def _load_users(self):
        # TODO This is really really bad
        with open('users.yaml', 'rb') as file:
            data = util.yaml.load(file)
        users = {id: User(self, id, **attrs) for id, attrs in data.items()}
        self._users = users

    def _save_users(self):
        users = {id: user.to_data() for id, user in self._users.items()}
        with open('users.yaml', 'wb') as file:
            util.yaml.dump(users, file)

    def send_text(self, user, text):
        if not isinstance(user, str):
            user = user.id
        self.updater.bot.send_message(user, text)

    def get_user(self, id):
        return self._users[id] if id in self._users else User(self, id)

    def get_context(self, *, update=None, data=None, cls=Context):
        if update:
            user = self.get_user(update.effective_user)
            return cls(self, user=user)
        if data:
            return cls(self, **data)

    def send_command(self, ctx, command, *args):
        ctx.reinvoked_commands.add(command)
        payload = {'op': 'COMMAND', 'd': {'command': command, 'context': ctx, 'arguments': args}}
        self.conn.send(payload)

    def send_message_command(self, user, message):
        payload = {'op': 'MESSAGE', 'd': {'user': user, 'message': Message(message)}}
        self.conn.send(payload)

    def message_listener(self, update, ctx):
        user = self.get_user(update.effective_user.id)
        if user in self.users and Game.PHASE is not Phase.PREPARING:
            message = update.message
            self.send_message_command(user, message)

    def process_payload(self):
        while True:
            payload = self.conn.recv()
            opcode, data = payload['op'], payload['d']
            if opcode == 'COMMAND':
                command, ctx, args = data['command'], data['context'], data['arguments']
                command.invoke(self, ctx, *args)
            if opcode == 'MESSAGE':
                user, message = data['user'], data['message']
                recipient = getattr(user, self.__class__.__name__.lower())
                message.send(recipient, bot=self)

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
        except Exception as error:
            if isinstance(error,  CommandError):
                if not error.quiet:
                    ctx.send(error.message)
            else:
                import traceback
                self.send_text(Game.ADMINS[0], traceback.format_exc())
                ctx.send('Bot有问题，err跟负责人讲一下')

    @classmethod
    def run(cls, token, conn):
        self = cls(token, conn)
        self._process_payload_thread = Thread(target=self.process_payload, daemon=True)
        self._process_payload_thread.start()
        self.updater.start_polling()

