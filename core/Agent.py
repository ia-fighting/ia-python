from GameEnvironment import ACTIONS


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
                self.__qtable[s][a] = {}
                for k in range(2):
                    self.__qtable[s][a][k % 2 == 0] = 0.0

    def _get_health(self):
        return self.__health

    def _set_health(self, health):
        self.__health = health

    def _get_state(self):
        return self.__state

    def _set_state(self, state):
        self.__state = state

    state = property(_get_state, _set_state)
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


    def update(self, action, new_state, has_neighbours, reward):
        # QTable update
        # Q(s, a) <- Q(s, a) + learning_rate * [reward + discount_factor * max(qtable[a]) - Q(s, a)]
        maxQ = 0.0
        # max of qtable
        for a in ACTIONS:
            if self.__qtable[new_state][a][has_neighbours] > maxQ:
                maxQ = self.__qtable[new_state][a][has_neighbours]
        LEARNING_RATE = 0.5
        DISCOUNT_FACTOR = 0.5

        self.__qtable[self.__state][action][has_neighbours] += LEARNING_RATE * \
                                               (reward + DISCOUNT_FACTOR * maxQ - self.__qtable[self.__state][action][has_neighbours])

        self.__state = new_state
        self.__score += reward
        self.__last_action = self.actual_action
        self.__actual_action = None

    # Best action who maximise reward
    def best_action(self, environment):
        possible_rewards = self.__qtable[self.__state]
        best = None
        for a in possible_rewards:
            has_neighbours = environment.is_near_players(self.__state)
            if best is None or possible_rewards[a][has_neighbours] > possible_rewards[best][has_neighbours]:
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

    @property
    def last_action(self):
        return self.__last_action

