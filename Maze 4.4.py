from random import *
import arcade
import pickle
import os

SPRITE_SIZE = 64

MAZE = """
    #.########
    #  #     #
    #  #  #  #
    #     #  #
    #$ ##### #
    #  #     *
    ##########
"""

BITCOIN = '$'
START = '.'
GOAL = '*'
WALL = '#'
UP = 'U'
DOWN = 'D'
LEFT = 'L'
RIGHT = 'R'
ACTIONS = [UP, DOWN, LEFT, RIGHT]

REWARD_OUT = -100
REWARD_BORDER = -10
REWARD_EMPTY = -1
REWARD_GOAL = 10
REWARD_BITCOIN = 10

class Environment:
    def __init__(self, text):
        self.__states = {}
        lines = list(map(lambda x: x.strip(), text.strip().split('\n')))
        for row in range(len(lines)):
            for col in range(len(lines[row])):
                self.__states[(row, col)] = lines[row][col]
                if(lines[row][col] == GOAL):
                    self.__goal = (row, col)
                if(lines[row][col] == START):
                    self.__start = (row, col)
        self.width = len(lines[0])
        self.height = len(lines)

    def reset(self):
        self.__states[(4, 1)] = BITCOIN
                
    @property
    def start(self):
        return self.__start

    @property
    def goal(self):
        return self.__goal

    @property
    def states(self):
        return self.__states.keys()

    def getContent(self, state):
        return self.__states[state]

    #Appliquer une action sur l'environnement
    #On met à jour l'état de l'agent, on lui donne sa récompense
    def apply(self, agent, action):
        state = agent.state
        if action == UP:
            new_state = (state[0] - 1, state[1])
        elif action == DOWN:
            new_state = (state[0] + 1, state[1])
        elif action == LEFT:
            new_state = (state[0], state[1] - 1)
        elif action == RIGHT:
            new_state = (state[0], state[1] + 1)

        #Calculer la récompense pour l'agent et la lui transmettre
        if new_state in self.__states :#and self.__states[new_state] not in [START, WALL]:
            if self.__states[new_state] in [WALL, START]:
                reward = REWARD_BORDER
            elif self.__states[new_state] == GOAL:
                reward = REWARD_GOAL
            elif self.__states[new_state] == BITCOIN:
                reward = REWARD_BITCOIN
                self.__states[new_state] = ' '
            else:
                reward = REWARD_EMPTY
            state = new_state
        else:
            reward = REWARD_OUT

        agent.update(action, state, reward)
        return reward

class Agent:
    def __init__(self, environment):
        self.__environment = environment
        self.__qtable = {}
        self.__learning_rate = 1
        self.__discount_factor = 1
        for s in environment.states:
            self.__qtable[s] = {}
            for a in ACTIONS:
                self.__qtable[s][a] = random() * 10.0
        self.reset()

    def save(self, filename):
        with open(filename, 'wb') as file:
            pickle.dump(self.__qtable, file)

    def load(self, filename):
        with open(filename, 'rb') as file:
            self.__qtable = pickle.load(file)            

    def reset(self):
        self.__state = self.__environment.start
        self.__score = 0
        self.__last_action = None

    def update(self, action, state, reward):
        #update q-table
        #Q(st, a) <- Q(st, a) + learning_rate *
        #                       [reward + discount_factor * max(qtable[st+1]) - Q(st, a)]
        maxQ = max(self.__qtable[state].values())
        self.__qtable[self.__state][action] += self.__learning_rate * \
                                (reward + self.__discount_factor * \
                                 maxQ - self.__qtable[self.__state][action])
        
        self.__state = state
        self.__score += reward
        self.__last_action = action

    def best_action(self):
        rewards = self.__qtable[self.__state]
        best = None
        for a in rewards:
            if best is None or rewards[a] > rewards[best]:
                best = a
        return best

    def do(self, action):
        self.__environment.apply(self, action)

    @property
    def state(self):
        return self.__state

    @property
    def score(self):
        return self.__score

    @property
    def qtable(self):
        return self.__qtable

    @property
    def environment(self):
        return self.__environment

class MazeWindow(arcade.Window):
    def __init__(self, agent):
        super().__init__(agent.environment.width * SPRITE_SIZE,
                         agent.environment.height * SPRITE_SIZE,
                         'ESGI Maze')
        self.__environment = agent.environment
        self.__agent = agent
        self.__iteration = 1

    #pour initialiser
    def setup(self):
        self.walls = arcade.SpriteList()
        for state in self.__environment.states:
            if self.__environment.getContent(state) == WALL:
                sprite = arcade.Sprite(":resources:images/tiles/stone.png", 0.5)
                sprite.center_x = (state[1] + 0.5) * SPRITE_SIZE
                sprite.center_y = self.height - (state[0] + 0.5) * SPRITE_SIZE
                self.walls.append(sprite)
                
        self.goal = arcade.Sprite(":resources:images/items/flagRed1.png", 0.5)
        self.goal.center_x = (self.__environment.goal[1] + 0.5) * SPRITE_SIZE
        self.goal.center_y = self.height - (self.__environment.goal[0] + 0.5) * SPRITE_SIZE

        self.player = arcade.Sprite(":resources:images/animated_characters/zombie/zombie_fall.png", 0.5)
        self.update_agent()

    def update_agent(self):
        self.player.center_x = (self.__agent.state[1] + 0.5) * SPRITE_SIZE
        self.player.center_y = self.height - (self.__agent.state[0] + 0.5) * SPRITE_SIZE

    #pour dessiner
    def on_draw(self):
        arcade.start_render()
        self.walls.draw()
        self.goal.draw()
        self.player.draw()
        arcade.draw_text(f"#{self.__iteration} Score : {self.__agent.score}",
                         10, 10, arcade.csscolor.WHITE, 20)

    def on_update(self, delta_time):
        #boucle d'apprentissage et d'action
        if self.__agent.state != self.__agent.environment.goal:
            action = self.__agent.best_action()
            reward = self.__agent.do(action)
            self.update_agent()

    def on_key_press(self, key, modifiers):
        if key == arcade.key.R:
            self.__agent.reset()
            self.__iteration += 1
            #on réinitialise l'agent (pas sa Q-table !)

if __name__ == "__main__":
    agent_filename = 'agent.dat'

    env = Environment(MAZE)
    agent = Agent(env)
    if os.path.exists(agent_filename):
        agent.load(agent_filename)
    
    window = MazeWindow(agent)
    window.setup()
    arcade.run()

    agent.save(agent_filename)
