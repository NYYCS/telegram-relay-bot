import enum

import util


class Phase(enum.Enum):
    PREPARING = "PREPARING"
    IN_PROGRESS = "IN_PROGRESS"
    ENDING = "ENDING"


class _Game:

    def __init__(self):
        with open('game.yaml', 'rb') as file:
            game = util.yaml.load(file)
        self.ADMINS = game['admins']
        self.PHASE = Phase(game['phase'])

    def set_phase(self, phase):
        self.PHASE = Phase(phase)
        with open('game.yaml', 'wb') as file:
            data = {
                'admins': self.ADMINS,
                'phase': self.PHASE.value
            }
            util.yaml.dump(data, file)


Game = _Game()
