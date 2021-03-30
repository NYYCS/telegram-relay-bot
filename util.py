import random

import ruamel.yaml

yaml = ruamel.yaml.YAML()


def shuffled(l):
    copy = l.copy()
    random.shuffle(copy)
    return copy
