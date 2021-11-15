# Game environment class

ARENA = """
#.              *     #
"""

START = '.'
GOAL = '*'
WALL = '#'

# Rewards
REWARD_OUT = -25
REWARD_TOUCH_TARGET = -25
REWARD_EMPTY = -1
REWARD_BLOCK = -5
REWARD_WOUND_TARGET = 10
REWARD_KILL_TARGET = 100
REWARD_BEING_TOUCH = -20
REWARD_TOUCH_EMPTY = -3

# Possible actions
RIGHT = 'R'
LEFT = 'L'
PUNCH = 'P'
BLOCK = 'B'
ACTIONS = [RIGHT, LEFT, PUNCH, BLOCK]


class Environment:
    def __init__(self, name):
        self.name = name
