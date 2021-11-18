# Game environment class
import time
from utils.Singleton import Singleton
import os

ARENA = """#*           *#"""

#TODO: QUESTION mettre plusieurs joueurs sur la map

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
                    agent.health -= 20
                    print("{} has been wounded".format(agent.health))
                    reward += REWARD_BEING_TOUCH
                    if agent.health <= 0:
                        self.__players.remove(agent)
                        reward += REWARD_KILL_TARGET
                else:
                    reward += REWARD_TOUCH_EMPTY
        return reward

    #list of player state
    @property
    def get_players_state(self):
        return [player.state for player in self.players]

    # Appliquer une action sur l'environnement
    # On met à jour l'état de l'agent, on lui donne sa récompense
    def apply(self, agent):
        state = agent.state
        action = agent.actual_action
        new_state = self.moving_agent(state, action)
        # Calcul recompense agent et lui transmettre
        if new_state in self.__states:
            if self.__states[new_state] in [WALL] or new_state[1] > len(ARENA) or new_state[1] < 0:
                reward = REWARD_OUT
            elif new_state in self.get_players_state:
                reward = REWARD_OUT
            elif action == PUNCH and self.is_near_players(new_state):
                print("BLOOOOOOOOOOOOOPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPP")
                reward = self.attack_near_players(new_state)
            elif action == BLOCK:
                reward = REWARD_BLOCK
            else:
                reward = REWARD_EMPTY
            state = new_state
        else:
            reward = REWARD_OUT
        agent.update(action, state, reward)
        return reward

    def display(self, generation, iteration, width):
        os.system('cls')
        incr = 0
        print('GEN: ', generation)
        print("ITERATION: ", iteration)
        print()
        for s in self.__states:
            incr += 1
            if s in self.get_players_state:
                print('P', end='')
            elif self.__states[s] == PLAYER:
                print(' ', end='')
            else:
                print(self.__states[s], end='')
            if incr % width == 0:
                print()
        print()


class Agent:
    def __init__(self, environment, health, position):
        self.__state = position
        self.__score = 0
        self.__last_action = None
        self.__qtable = {}
        self.__health = health
        self.__actual_action = None

        # QTable initialization
        for s in environment.states:
            self.__qtable[s] = {}
            for a in ACTIONS:
                self.__qtable[s][a] = 0.0

    def _get_health(self):
        return self.__health

    def _set_health(self, health):
        self.__health = health

    health = property(_get_health, _set_health)

    def is_alive(self):
        if self.__health <= 0:
            return False
        return True

    def _get_actual_action(self):
        return self.__actual_action

    def _set_actual_action(self, actual_action):
        self.__actual_action = actual_action

    actual_action = property(_get_actual_action, _set_actual_action)


    def update(self, action, new_state, reward):
        # QTable update
        # Q(s, a) <- Q(s, a) + learning_rate * [reward + discount_factor * max(qtable[a]) - Q(s, a)]
        maxQ = max(self.__qtable[new_state].values())
        LEARNING_RATE = 1
        DISCOUNT_FACTOR = 0.5

        self.__qtable[self.__state][action] += LEARNING_RATE * \
                                               (reward + DISCOUNT_FACTOR * maxQ - self.__qtable[self.__state][action])

        self.__state = new_state
        self.__score += reward
        self.__last_action = self.actual_action
        self.__actual_action = None

    # Best action who maximise reward
    def best_action(self):
        possible_rewards = self.__qtable[self.__state]
        best = None
        for a in possible_rewards:
            if best is None or possible_rewards[a] > possible_rewards[best]:
                best = a
                self.__actual_action = best

    @property
    def state(self):
        return self.__state

    @property
    def score(self):
        return self.__score

    @property
    def qtable(self):
        return self.__qtable

    def reset(self, environment):
        self.__state = environment.start


class AgentManager:
    def __init__(self, environment, population, health):
        self.__environment = environment
        self.__population = population
        self.__agents = []
        for i in range(population):
            self.__agents.append(Agent(self.__environment, health, self.__environment.players_pos[i]))
            self.__environment.players = self.__agents

    # Verify if all agents are alive
    def is_only_one_agent_alive(self):
        count = 0
        for a in self.__agents:
            if a.is_alive():
                count += 1
        # if count superior to 1, there is more than one agent alive
        if count > 1:
            return False
        return True

    @property
    def get_agents(self):
        return self.__agents

    # get all alive agents
    @property
    def get_alive_agents(self):
        alive_agents = []
        for a in self.__agents:
            if a.is_alive():
                alive_agents.append(a)
        return alive_agents

    @property
    def goal(self):
        return self.is_only_one_agent_alive()

    # Best action for each agent
    def best_actions(self):
        for a in self.__agents:
            if a.is_alive():
                a.best_action()

    def apply_actions(self, agents):
        # Apply moving actions
        for i in range(len(agents)):
            agent = agents[i]
            print('Agent ', i, ' action :', agent.actual_action)
            print('Agent ', i, ' health :', agent.health)
            if agent.is_alive():
                if agent.actual_action in MOVING_ACTIONS:
                    self.__environment.apply(agents[i])
        # Apply others actions
        #print(self.__environment.get_players_state)
        for i in range(len(agents)):
            agent = agents[i]
            if agents[i].is_alive():
                if agent.actual_action not in MOVING_ACTIONS and agent.actual_action is not None:
                    self.__environment.apply(agent)


if __name__ == '__main__':
    env = GameEnvironment(ARENA)

    # initialize AgentManager
    am = AgentManager(env, 2, 80)
    print(env.states)

    for i in range(1):
        print('GEN: ', i)
        iteration = 0
        while not am.goal:
            iteration += 1
            am.best_actions()
            am.apply_actions(am.get_alive_agents)
            #if iteration % 1000 == 0:
                #print('iteration :', iteration)
            if (i == 0):
                time.sleep(0.3)
                env.display(i, iteration, len(list(map(lambda x: x.strip(), ARENA.strip().split('\n')))[0]))
