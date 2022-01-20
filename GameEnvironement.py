from core.utils.Singleton import Singleton
from Environment import *

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

    def attack_players(self, agent, new_state):
        reward = 0
        for target in self.players:
            if target.state != new_state:
                reward = agent.attack(new_state, target)
                if target.health <= 0:
                    reward += REWARD_KILL_TARGET
                    target.is_alive = False
        return reward

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

    def other_players_state(self, new_state):
        players_state = self.get_players_state.copy()
        # remove state from get_players_state
        if new_state in self.get_players_state:
            players_state.remove(new_state)
        return players_state

    # Appliquer une action sur l'environnement
    # On met à jour l'état de l'agent, on lui donne sa récompense
    def apply(self, agent, opponent):
        reward = 0
        state = agent.state
        action = agent.actual_action
        if not agent.is_alive:
            reward = REWARD_DEATH
        else:
            new_state = self.moving_agent(state, action)
            # Calcul recompense agent et lui transmettre
            if new_state in self.__states:
                if self.__states[new_state] in [WALL] or new_state[1] > len(ARENA) or new_state[1] < 0:
                    reward = REWARD_OUT
                elif new_state in self.other_players_state(new_state):
                    reward = REWARD_OUT
                elif action == PUNCH and self.is_near_players(state):
                    reward = self.attack_players(agent, new_state)
                elif action == PUNCH:
                    reward = REWARD_TOUCH_EMPTY
                elif action == BLOCK:
                    reward = self.do_action_bloc(agent, opponent)
                else:
                    reward = REWARD_EMPTY
                state = new_state
            else:
                reward = REWARD_OUT
        # print(f"action: {action}, reward: {reward}, is alive: {agent.is_alive}")
        agent.update_ia(action, state, opponent, reward)
        return reward

    def do_action_bloc(self, agent, opponent):
        if opponent.actual_action is not None:
            if opponent.actual_action == PUNCH and self.is_near_players(opponent.state):
                return REWARD_BLOCK_ATTACK
            else:
                return REWARD_BLOCK
        elif opponent.last_action == PUNCH and self.is_near_players(opponent.state):
            return REWARD_BLOCK_ATTACK
        else:
            return REWARD_BLOCK

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

    # list of player state
    @property
    def get_players_state(self):
        return [player.state for player in self.players]

