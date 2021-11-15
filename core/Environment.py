# Game environment class

ARENA = """
#.              *     #
"""

START = '.'
TARGET = '*'
WALL = '#'

# Rewards
REWARD_OUT = -25
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

class Target:
    def __init__(self, health):
        self.__health = health

    def _get_health(self):
        return self.__health

    def _set_health(self, health):
        self.__health = health

    name = property(_get_health, _set_health)

class Game:
    def __init__(self, agent, text_arena):
        self.agent = agent
        self.__states = {}

        # Environment parsing
        lines = list(map(lambda x: x.strip(), text_arena.strip().split('\n')))
        for row in range(len(lines)):
            for col in range(len(lines[row])):
                self.__states[(row, col)] = lines[row][col]
                if lines[row][col] == TARGET:
                    self.__target = (row, col)
                if lines[row][col] == START:
                    self.__start = (row, col)

    @property
    def start(self):
        return self.__start

    @property
    def target(self):
        return self.__target

    @property
    def states(self):
        return self.__states.keys()

    # Appliquer une action sur l'environnement
    # On met à jour l'état de l'agent, on lui donne sa récompense
    def apply(self, agent, action):
        state = agent.state
        if action == LEFT:
            new_state = (state[0], state[1] - 1)
        if action == RIGHT:
            new_state = (state[0], state[1] + 1)

        #should not be inf or sup to the arena size
        right_state = (state[0], state[1] + 2)
        left_state = (state[0], state[1] - 2)
        # Calcul recompense agent et lui transmettre
        if new_state in self.__states:
            if self.__states[new_state] in [WALL, TARGET]:
                reward = REWARD_OUT
            elif self.__states[right_state] == TARGET and action == PUNCH:
                reward = REWARD_WOUND_TARGET
                #target health - 20
            elif self.__states[left_state] == TARGET and action == PUNCH:
                reward = REWARD_WOUND_TARGET
                # target health - 20
            elif action == BLOCK:
                reward = REWARD_BLOCK
            else:
                reward = REWARD_EMPTY
            #if target health <= 0 : reward kill
            state = new_state
        else:
            reward = REWARD_OUT
        agent.update(action, state, reward)
        return reward

