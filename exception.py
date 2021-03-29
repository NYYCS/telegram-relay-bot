class BotException(Exception):
    pass


class CommandError(BotException):
    pass


class CommandUsageError(CommandError):
    pass
