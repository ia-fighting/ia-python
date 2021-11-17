# Game environment class
import time
import os

ARENA = """#.              *     #"""

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

    def is_alive(self):
        if self.__health <= 0:
            return False
        return True

    health = property(_get_health, _set_health)


class GameEnvironment:
    def __init__(self, target, text_arena):
        self.__target = target
        self.__target_start = Target(target.health)
        self.__states = {}

        # Environment parsing
        lines = list(map(lambda x: x.strip(), text_arena.strip().split('\n')))
        for row in range(len(lines)):
            for col in range(len(lines[row])):
                self.__states[(row, col)] = lines[row][col]
                if lines[row][col] == TARGET:
                    self.__target_pos = (row, col)
                if lines[row][col] == START:
                    self.__start = (row, col)

    @property
    def start(self):
        return self.__start

    @property
    def target_pos(self):
        return self.__target_pos

    def _get_target(self):
        return self.__target

    def _set_target(self, target):
        self.__target = target

    target = property(_get_target, _set_target)

    @property
    def target_start(self):
        return self.__target_start

    @property
    def states(self):
        return self.__states.keys()

    @property
    def goal(self):
        return not self.__target.is_alive()

    def is_near_target(self, state, states):
        if state[1] < len(ARENA) - 1:
            if states[(state[0], state[1] + 1)] in [TARGET]:
                return True
        if state[1] >= 1:
            if states[(state[0], state[1] - 1)] in [TARGET]:
                return True
        return False

    # Appliquer une action sur l'environnement
    # On met à jour l'état de l'agent, on lui donne sa récompense
    def apply(self, agent, action):
        state = agent.state
        if action == LEFT:
            new_state = (state[0], state[1] - 1)
        elif action == RIGHT:
            new_state = (state[0], state[1] + 1)
        else:
            new_state = state
        # Calcul recompense agent et lui transmettre
        if new_state in self.__states:
            if self.__states[new_state] in [WALL, TARGET] or new_state[1] > len(ARENA) or new_state[1] < 0:
                reward = REWARD_OUT
            elif action == PUNCH and self.is_near_target(state, self.__states):
                reward = REWARD_WOUND_TARGET
                self.target.health -= 20
            elif action == BLOCK:
                reward = REWARD_BLOCK
            else:
                reward = REWARD_EMPTY
            if not self.target.is_alive():
                reward = REWARD_KILL_TARGET
            state = new_state
        else:
            reward = REWARD_OUT
        agent.update(action, state, reward)
        return reward

    def display(self, position, generation, iteration, width):
        os.system('cls')
        incr = 0
        print('GEN: ', generation)
        print("ITERATION: ", iteration)
        print()
        for s in self.__states:
            incr += 1
            if position == s:
                print('P', end='')
            else:
                print(self.__states[s], end='')
            if incr % width == 0:
                print()
        print()


class Agent:
    def __init__(self, environment, health):
        self.__state = environment.start
        self.__score = 0
        self.__last_action = None
        self.__qtable = {}
        self.__health = health

        # QTable initialization
        for s in environment.states:
            self.__qtable[s] = {}
            for a in ACTIONS:
                self.__qtable[s][a] = 0.0

    def _get_health(self):
        return self.__health

    def _set_health(self, health):
        self.__health = health

    def is_alive(self):
        if self.__health <= 0:
            return False
        return True

    health = property(_get_health, _set_health)

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
        self.__last_action = action

    # Best action who maximise reward
    def best_action(self):
        possible_rewards = self.__qtable[self.__state]
        best = None
        for a in possible_rewards:
            if best is None or possible_rewards[a] > possible_rewards[best]:
                best = a
        return best

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
        environment.target = Target(environment.target_start.health)


if __name__ == '__main__':
    target = Target(60)
    env = GameEnvironment(target, ARENA)
    print(env.states)

    agent = Agent(env, 60)

    for i in range(100):
        print('GEN: ', i)
        agent.reset(env)
        iteration = 0
        while not env.goal:
            iteration += 1
            action = agent.best_action()
            reward = env.apply(agent, action)
            if (i == 99):
                time.sleep(0.2)
                env.display(agent.state, i, iteration,
                    len(list(map(lambda x: x.strip(), ARENA.strip().split('\n')))[0]))
