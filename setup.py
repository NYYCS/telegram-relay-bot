import random
from ruamel.yaml import YAML
import json

yaml = YAML()

with open('members.yaml', 'r') as f:
    members = yaml.load(f)
    while True:
        a, b = list(members.keys()), list(members.keys())
        random.shuffle(a)
        random.shuffle(b)
        paired = {}
        for x, y in zip(a, b):
            if x == y:
                pass
            paired[x] = y
        break

with open('angel_score.json', 'w+') as f1:
    with open('host_score.json', 'w+') as f2:
        scores = {}
        for member in members.keys():
            scores[member] = 0
        json.dump(scores, f1)
        json.dump(scores, f2)


with open('angels.yaml', 'w') as f:
    yaml.dump(paired, f)

with open('hosts.yaml', 'w') as f:
    inverted = { v: k for k, v in paired.items() }
    yaml.dump(paired, f)


