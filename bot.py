from telegram.ext import Updater, MessageHandler, Filters

from threading import Thread

import logging
import random
import os

from commands import Command, CommandError
from message import Message
from context import Context
from game import Game, Phase
from user import User

import util

logging.basicConfig(filename='app.log', filemode='a', format='%(name)s:%(module)s - %(levelname)s - %(message)s', level=20)

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
        self.log = logging.getLogger(cls.__name__.upper())
        return self

    def try_dump(self, filename, data):
        tempfile = "%s.yaml" % random.randint(100000, 999999)
        try:
            with open(tempfile, 'wb') as file:
                util.yaml.dump(data, file)
        except Exception:
            import traceback
            self.log.critical("Exception occured when loading '%s'!" % filename, exc_info=True)
            self.send_text(Game.ADMINS[0], traceback.format_exc())
        else:
            with open(filename, 'wb') as file:
                util.yaml.dump(data, file)
        finally:
            os.remove(tempfile)

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
        self.log.info("Loading users...")
        with open('users.yaml', 'rb') as file:
            data = util.yaml.load(file)
        users = {id: User(self, **attrs) for id, attrs in data.items()}
        self._users = users
        self.log.info("Users loaded.")

    def _save_users(self):
        self.log.info("Saving users...")
        users = {id: user.to_data() for id, user in self._users.items()}
        self.try_dump('users.yaml', users)
        self.log.info("Users saved.")

    def send_text(self, user, text):
        if not isinstance(user, int):
            user = user.id
        self.updater.bot.send_message(user, text)

    def send_photo(self, user, filename):
        self.updater.bot.send_photo(user.id, open(filename,'rb'))

    def get_user(self, id):
        return self._users[id] if id in self._users else User(self, id)

    def get_context(self, *, update=None, data=None, cls=Context):
        if update:
            user = self.get_user(update.effective_user.id)
            return cls(self, user=user)
        if data:
            return cls(self, **data)

    def send_command(self, command, ctx, *args):
        ctx.reinvoked_commands.add(command)
        payload = {'op': 'COMMAND', 'd': {'command': command, 'context': ctx.to_data(), 'arguments': args}}
        self.conn.send(payload)

    def send_message_command(self, user, message):
        payload = {'op': 'MESSAGE', 'd': {'user': user.id, 'message': Message(message).to_data()}}
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
                self.log.info("Received COMMAND payload.")
                command, ctx, args = self.commands.get(data['command']), self.get_context(data=data['context']), data['arguments']
                command.invoke(self, ctx, *args)
            if opcode == 'MESSAGE':
                self.log.info("Received MESSAGE payload.")
                user, message = self.get_user(data['user']), Message(**data['message'])
                if self.__class__.__name__ == "Sender":
                    message.send(user.sender.id, bot=self)
                if self.__class__.__name__ == "Recipient":
                    message.send(user.recipient.id, bot=self)
            if opcode == 'SYNC':
                self.log.info("Syncing users.")
                self._load_users()

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
            self.log.info("Invoking %s" % command)
            command.invoke(self, ctx, *args)
        except Exception as error:
            if isinstance(error,  CommandError):
                ctx.reply(error.__traceback__)
            else:
                import traceback
                self.log.critical("Exception occurred when invoking %s" % command, exc_info=True)
                self.send_text(Game.ADMINS[0], traceback.format_exc())
                ctx.reply('Bot有问题，err跟负责人讲一下')

    @classmethod
    def run(cls, token, conn):
        self = cls(token, conn)
        self.log.info("Running...")
        self._process_payload_thread = Thread(target=self.process_payload, daemon=True)
        self._process_payload_thread.start()
        self.updater.start_polling()

