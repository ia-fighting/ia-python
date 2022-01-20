from Environment import *
from Agent import *

class AgentManager:
    def __init__(self, environment, population, health):
        self.__environment = environment
        self.__population = population
        self.__player_1_has_priority = PLAYER_1_HAS_PRIORITY
        self.__health = health
        self.__agents = []
        self.set_new_agents()

    def set_new_agents(self):
        qtable1 = None
        qtable2 = None
        if len(self.__agents) > 1:
            qtable1 = self.__agents[0].qtable
            qtable2 = self.__agents[1].qtable
        self.__agents.clear()
        for i in range(self.__population):
            if i % 2 == 0:
                self.__agents.append(Agent(self.__environment, MAX_HP,
                                           self.__environment.players_pos[i], 'male', RIGHT_FACING, qtable1, i))
            else:
                self.__agents.append(
                    Agent(self.__environment, MAX_HP,
                          self.__environment.players_pos[i], 'female', LEFT_FACING, qtable2, i))
        self.__environment.players = self.__agents

    # Verify if all agents are alive
    def is_only_one_agent_alive(self):
        count = 0
        for a in self.__agents:
            if a.is_alive:
                count += 1
        # if count superior to 1, there is more than one agent alive
        if count > 1:
            return False
        return True

    def _get_agents(self):
        return self.__agents

    def _set_agents(self, agents):
        self.__agents = agents

    agents = property(_get_agents, _set_agents)

    @property
    def get_agents_health(self):
        return self.__health

    def reset(self):
        # for each agent, reset the health and the state
        self.set_new_agents()

    def _get_player_1_has_priority(self):
        return self.__player_1_has_priority

    def _set_player_1_has_priority(self, value):
        self.__player_1_has_priority = value

    player_1_priority = property(_get_player_1_has_priority, _set_player_1_has_priority)

    # get all alive agents
    @property
    def get_alive_agents(self):
        alive_agents = []
        for a in self.__agents:
            if a.is_alive:
                alive_agents.append(a)
        return alive_agents

    @property
    def goal(self):
        return self.is_only_one_agent_alive()

    def get_opponent(self, agent):
        for a in self.__agents:
            if a != agent:
                return a

    # Best action for each agent
    def best_actions(self):
        for a in self.__agents:
            if a.is_alive:
                a.best_action(self.get_opponent(a))

    def apply_actions(self, agents):
        # Apply moving actions
        if self.player_1_priority:
            for i in range(len(agents)):
                agent = agents[i]
                actual_action = agent.actual_action
                if actual_action in MOVING_ACTIONS:
                    self.__environment.apply(agents[i], self.get_opponent(agents[i]))
            # Apply others actions
            for i in range(len(agents)):
                agent = agents[i]
                actual_action = agent.actual_action
                if actual_action not in MOVING_ACTIONS and actual_action is not None:
                    self.__environment.apply(agent, self.get_opponent(agents[i]))
        else:
            for i in range(len(agents)):
                agent = agents[(i+1) % 2]
                actual_action = agent.actual_action
                if actual_action in MOVING_ACTIONS:
                    self.__environment.apply(agents[(i+1) % 2], self.get_opponent(agents[(i+1) % 2]))
            # Apply others actions
            for i in range(len(agents)):
                agent = agents[(i+1) % 2]
                actual_action = agent.actual_action
                if actual_action not in MOVING_ACTIONS and actual_action is not None:
                    self.__environment.apply(agent, self.get_opponent(agents[(i+1) % 2]))

