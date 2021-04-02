import util

with open("game.yaml", 'wb') as file:
    util.yaml.dump({
        'admins': [],
        'phase': 'PREPARING'
    })

with open("users.yaml", 'wb') as file:
    util.yaml.dump({})