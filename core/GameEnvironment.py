# Game environment class
from utils.Singleton import Singleton

ARENA = """#*       *#"""

PLAYER = '*'
WALL = '#'

# Rewards
REWARD_OUT = -25
REWARD_EMPTY = -1
REWARD_BLOCK = -5
REWARD_WOUND_TARGET = 30
REWARD_KILL_TARGET = 100
REWARD_BEING_TOUCH = -20
REWARD_TOUCH_EMPTY = -2

# Possible actions
RIGHT = 'R'
LEFT = 'L'
PUNCH = 'P'
BLOCK = 'B'
ACTIONS = [RIGHT, LEFT, PUNCH, BLOCK]
MOVING_ACTIONS = [RIGHT, LEFT]


class GameEnvironment(Singleton):
    def __init__(self, text_arena):
        self.__states = {}
        self.__players_pos = []
        self.__players = []

        # Environment parsing
        lines = list(map(lambda x: x.strip(), text_arena.strip().split('\n')))
        for row in range(len(lines)):
            for col in range(len(lines[row])):
                self.__states[(row, col)] = lines[row][col]
                if lines[row][col] == PLAYER:
                    self.__players_pos.append((row, col))
        self.__players_pos_start = self.__players_pos.copy()


    @property
    def players_pos(self):
        return self.__players_pos

    def _get_players(self):
        return self.__players

    def _set_players(self, players):
        self.__players = players

    players = property(_get_players, _set_players)

    @property
    def players_pos_start(self):
        return self.__players_pos_start

    @property
    def states(self):
        return self.__states.keys()

    @property
    def all_states(self):
        return self.__states

    def is_near_players(self, state):
        if state[1] < len(ARENA) - 1:
            if (state[0], state[1] + 1) in self.get_players_state:
                return True
        if state[1] >= 1:
            if (state[0], state[1] - 1) in self.get_players_state:
                return True
        return False

    def moving_agent(self, state, action):
        if action == LEFT:
            new_state = (state[0], state[1] - 1)
        elif action == RIGHT:
            new_state = (state[0], state[1] + 1)
        else:
            new_state = state
        return new_state

    # fetch agent at position
    def get_agent(self, state):
        for agent in self.__players:
            if agent.state == state:
                return agent

    def attack_near_players(self, new_state):
        reward = 0
        for agent in self.__players:
            if agent.state == (new_state[0], new_state[1] - 1) \
                    or agent.state == (new_state[0], new_state[1] + 1):
                if agent.actual_action != BLOCK:
                    agent.health = agent.health - 20
                    reward += REWARD_BEING_TOUCH
                    if agent.health <= 0:
                        self.__players.remove(agent)
                        reward += REWARD_KILL_TARGET
                else:
                    reward = REWARD_TOUCH_EMPTY
        return reward

    #list of player state
    @property
    def get_players_state(self):
        return [player.state for player in self.players]


    def other_players_state(self, new_state):
        players_state = self.get_players_state.copy()
        #remove state from get_players_state
        if new_state in self.get_players_state:
            players_state.remove(new_state)
        return players_state

    # Appliquer une action sur l'environnement
    # On met à jour l'état de l'agent, on lui donne sa récompense
    def apply(self, agent):
        state = agent.state
        has_neighbours = self.is_near_players(state)
        action = agent.actual_action
        new_state = self.moving_agent(state, action)
        # Calcul recompense agent et lui transmettre
        if new_state in self.__states:
            if self.__states[new_state] in [WALL] or new_state[1] > len(ARENA) or new_state[1] < 0:
                reward = REWARD_OUT
            elif new_state in self.other_players_state(new_state):
                reward = REWARD_OUT
            elif action == PUNCH and self.is_near_players(state):
                reward = self.attack_near_players(new_state)
            elif action == BLOCK:
                reward = REWARD_BLOCK
            else:
                reward = REWARD_EMPTY
            state = new_state
        else:
            reward = REWARD_OUT
        agent.update(action, state, has_neighbours, reward)
        return reward
