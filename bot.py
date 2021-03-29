from telegram.ext import Updater, MessageHandler, Filters

import util
from commands import Command
from context import Context
from exception import CommandUsageError


class User:

    def __init__(self, id, **attrs):
        self.id = id
        self.name = attrs.pop('name', 'UNSIGNED')
        self._recipient = attrs.pop('recipient', None)
        self._sender = attrs.pop('sender', None)

    def __hash__(self):
        return self.id

    def __eq__(self, other):
        return self.id == other.id and isinstance(other, self.__class__)

    def __str__(self):
        return self.name

    def to_data(self):
        return dict((() for attr in ('id', 'name', 'recipient', 'sender')))


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
        self._users[id] = User(id=id, name=name)
        users = {id: user.name for id, user in self._users.items()}
        with open('users.yaml', 'wb') as file:
            util.yaml.dump(users, file)

    def _load_users(self):
        # TODO This is really really bad
        with open('users.yaml', 'rb') as file:
            data = util.yaml.load(file)
        users = {id: User(**attrs) for id, attrs in data.items()}
        self._users = users

        for user in self.users:
            if user._recipient is None:
                break
            user.recipient = self._users[user._recipient]
            user.sender = self._users[user._sender]

    def get_user(self, id):
        return self._users[id] if id in self._users else User(id)

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
            'd': {
                'command': command,
                'context': ctx.to_dict(),
                'arguments': args
            }
        }
        self.conn.send(payload)

    def process_message(self, message):
        if message.text:
            pass

    def message_listener(self, update, ctx):
        message = update.message

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
