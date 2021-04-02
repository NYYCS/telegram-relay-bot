import random

import ruamel.yaml
import logging

log = logging.getLogger()

yaml = ruamel.yaml.YAML()


def shuffled(l):
    copy = l.copy()
    random.shuffle(copy)
    return copy

