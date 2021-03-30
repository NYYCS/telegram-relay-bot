import inspect

from exception import BotException


class CommandError(BotException):

    def __init__(self, message, *, quiet=True):
        super().__init__(message)
        self.message = message
        self.quiet = quiet

class CommandUsageError(CommandError):

    def __init__(self, command):
        super().__init__(
            "命令用法错误！\n"
            "正确用法： `%s %s`" % (command.prefixed_name, command.usage)
        )


class CheckFailure(CommandError):

    def __init__(self, check):
        message = getattr(check, 'message', None)
        super().__init__(message, quiet=message is not None)



def command(*, name, reinvoke=False):

    def wrapper(func):
        func.__command_attrs__ = {
            'name': name,
            'checks': command.__command_checks__ if hasattr(func, '__command_checks__') else None,
            'reinvoke': reinvoke
        }
        return func

    return wrapper


def check(predicate, *, message=None):

    if message:
        predicate.message = message

    def wrapper(func):
        if isinstance(func, Command):
            func.checks.append(predicate)
        else:
            if not hasattr(func, '__command_checks__'):
                func.__command_checks__ = []
            func.__command_checks__.append(predicate)

        return func

    return wrapper


class Command:

    def __init__(self, callback, name, *, checks=None, reinvoke=False):
        self.callback = callback
        self.name = name
        self.prefixed_name = "/" + self.name
        self.reinvoke = reinvoke

        argnames, varargs, *_, annotations = inspect.getfullargspec(self.callback)

        self._varargs = varargs

        if self._varargs:
            self.usage = "`%s [arguments]`" % self.prefixed_name
        else:
            self.usage = "`%s %s" % (self.prefixed_name, " ".join(argnames))
            # TODO make this not as scuffed?
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
                raise CheckFailure(check)

        if self._varargs:
            self.callback(bot, ctx, *args)
        else:
            cleaned = []

            for arg, converter in zip(args[:len(self.converters)], self.converters):
                if converter is not None:
                    try:
                        arg = converter(arg)
                    except:
                        raise CommandUsageError(self)
                cleaned.append(arg)

            self.callback(bot, ctx, *cleaned)

        if self.reinvoke and self.name in ctx.reinvoked_commands:
            bot.send_command(self.name, ctx, *args)
