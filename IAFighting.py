# Project main class
# IAFighting.py class

from core.GameEnvironment import ARENA
from core.GameEnvironment import GameEnvironment
from core.AgentManager import AgentManager
import time


if __name__ == '__main__':

    def display_iteration(generation, iter):
        if generation == 9:
            time.sleep(0.3)
            am.display(i, iter, len(list(map(lambda x: x.strip(), ARENA.strip().split('\n')))[0]))

    env = GameEnvironment(ARENA)

    # initialize AgentManager
    am = AgentManager(env, 2, 80)
    print(env.states)

    for i in range(20):
        print('GEN: ', i)
        am.reset()
        iteration = 0
        while not am.goal:
            iteration += 1
            am.best_actions()
            am.apply_actions(am.get_alive_agents)

            #display_iteration(9, iteration)
        print('GEN: ', i, ' - ', iteration, ' iterations')
