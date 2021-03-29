import random

import ruamel.yaml

yaml = ruamel.yaml.YAML()


class cached_property:
    def __init__(self, function):
        self.function = function
        self.__doc__ = getattr(function, '__doc__')

    def __get__(self, instance, owner):
        if instance is None:
            return self

        value = self.function(instance)
        setattr(instance, self.function.__name__, value)

        return value


def shuffled(l):
    copy = l.copy()
    random.shuffle(copy)
    return copy
