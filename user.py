class User:

    def __init__(self, bot, id, **attrs):
        self.__bot = bot
        self.id = id
        self.name = attrs.pop('name', 'UNSIGNED')
        self._recipient = attrs.pop('recipient', None)
        self._sender = attrs.pop('sender', None)

    @property
    def recipient(self):
        return self.__bot.get_user(self._recipient)

    @property
    def sender(self):
        return self.__bot.get_user(self._sender)

    @recipient.setter
    def recipient(self, user):
        self._recipient = user.id

    @sender.setter
    def sender(self, user):
        self.sender = user.id

    def __hash__(self):
        return self.id

    def __eq__(self, other):
        return self.id == other.id and isinstance(other, self.__class__)

    def __str__(self):
        return self.name

    def to_data(self):
        return dict(((attr, self.__dict__[attr]) for attr in ('id', 'name', '_recipient', '_sender')))
