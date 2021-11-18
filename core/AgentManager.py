import os
from Agent import Agent
from GameEnvironment import PLAYER
from GameEnvironment import MOVING_ACTIONS


class AgentManager:
    def __init__(self, environment, population, health):
        self.__environment = environment
        self.__population = population
        self.__health = health
        self.__agents = []
        for i in range(self.__population):
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

    @property
    def get_agents_health(self):
        return self.__health

    def reset(self):
        # for each agent, reset the health and the state
        for i in range(len(self.get_agents)):
            self.__agents[i].health = self.get_agents_health
        for j in range(i + 1, self.__population):
            self.__agents.append(Agent(self.__environment, self.get_agents_health, self.__environment.players_pos[j]))
            self.__environment.players = self.__agents
        self.__environment.players = self.__agents
        self.__score = 0
        self.__last_action = None

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
                a.best_action(self.__environment)

    def apply_actions(self, agents):
        # Apply moving actions
        for i in range(len(agents)):
            agent = agents[i]
            if agent.is_alive():
                if agent.actual_action in MOVING_ACTIONS:
                    self.__environment.apply(agents[i])
        for i in range(len(agents)):
            agent = agents[i]
            if agents[i].is_alive():
                if agent.actual_action not in MOVING_ACTIONS and agent.actual_action is not None:
                    self.__environment.apply(agent)

    def display(self, generation, iteration, width):
        os.system('cls')
        incr = 0
        print('GEN: ', generation)
        print("ITERATION: ", iteration)
        print()
        for s in self.__environment.all_states:
            incr += 1
            if s in self.__environment.get_players_state:
                print('P', end='')
            elif self.__environment.all_states[s] == PLAYER:
                print(' ', end='')
            else:
                print(self.__environment.all_states[s], end='')
            if incr % width == 0:
                print()
        for i in range(len(self.__agents)):
            print('Agent ', i, ' health :', self.__agents[i].health)
            print('Agent ', i, ' action :', self.__agents[i].last_action)
        print()
