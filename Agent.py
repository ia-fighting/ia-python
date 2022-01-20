import os
import pickle

import arcade
from random import random, choice
from Environment import *

ATTACK_SOUND = arcade.load_sound(f"{SOUNDS_PATH}/attack_short.mp3")
HIT_SOUND = arcade.load_sound(f"{SOUNDS_PATH}/hit.mp3")
BLOCK_SOUND = arcade.load_sound(f"{SOUNDS_PATH}/block.mp3")
JUMP_SOUND = arcade.load_sound(f"{SOUNDS_PATH}/jump.mp3")


def load_texture_pair(filename):
    """
    Load a texture pair, with the second being a mirror image.
    """
    return [
        arcade.load_texture(filename),
        arcade.load_texture(filename, flipped_horizontally=True),
    ]


class Agent(arcade.Sprite):

    def __init__(self, environment, health, position, sprites, face_direction, qtable, agent_number):
        super().__init__()

        self.character_face_direction = face_direction
        self.__state = position
        self.__score = 0
        self.__last_action = None
        self.__qtable = {}
        self.__health = health
        self.__actual_action = None
        self.__health_bar = arcade.SpriteList(use_spatial_hash=True)
        self.__agent_number = agent_number

        self.__sprites = sprites

        # Used for flipping between image sequences
        self.__cur_texture = 0
        self.__cur_attack_texture = 0
        self.__cur_idle_texture = 0
        self.__cur_dead_texture = 0
        self.__change_x = 0
        self.__change_y = 0
        self.__exploration = 1.0
        self.scale = CHARACTER_SCALING

        # Track our state
        self.__is_on_ladder = False
        self.__is_attacking = False
        self.__is_touched = False
        self.__is_blocking = False
        self.__is_dead = False
        self.__is_alive = True
        self.__is_down = False

        self.walk_textures = []
        self.attack_textures = []
        self.idle_textures = []
        self.dead_textures = []

        # Load textures for idle standing
        self.idle_texture_pair = load_texture_pair(f"{MAIN_PATH}{self.__sprites}/Idle1.png")
        self.jump_texture_pair = load_texture_pair(f"{MAIN_PATH}{self.__sprites}/Dead3.png")
        self.fall_texture_pair = load_texture_pair(f"{MAIN_PATH}{self.__sprites}/Idle1.png")
        self.block_texture_pair = load_texture_pair(f"{MAIN_PATH}{self.__sprites}/Dead1.png")

        # Set up sprites animations for the agent
        self.set_up_agent_sprites()

        # QTable initialization
        if qtable is None:
            if os.path.isfile('../qtable_agent_' + str(self.agent_number) + '.dat'):
                self.load_qtable('../qtable_agent_' + str(self.agent_number))
            else:
                for s in environment.states:
                    self.__qtable[s] = {}
                    for a in ACTIONS:
                        self.__qtable[s][a] = {}
                        for s2 in environment.states:
                            self.__qtable[s][a][s2] = {}
                            for a2 in ACTIONS:
                                self.__qtable[s][a][s2][a2] = 0.0
        else:
            self.__qtable = qtable

    def set_up_agent_sprites(self):
        # Load textures for walking
        for i in range(1, 10):
            walk_texture = load_texture_pair(f"{MAIN_PATH}{self.__sprites}/Walk{i}.png")
            self.walk_textures.append(walk_texture)

        # Load textures for attacking
        for i in range(1, 8):
            attack_texture = load_texture_pair(f"{MAIN_PATH}{self.__sprites}/Attack{i}.png")
            self.attack_textures.append(attack_texture)

        for i in range(1, 16):
            idle_texture = load_texture_pair(f"{MAIN_PATH}{self.__sprites}/Idle{i}.png")
            self.idle_textures.append(idle_texture)

        for i in range(1, 13):
            dead_texture = load_texture_pair(f"{MAIN_PATH}{self.__sprites}/Dead{i}.png")
            self.dead_textures.append(dead_texture)

        # Set the initial texture
        if not self.__is_attacking:
            self.texture = self.idle_texture_pair[0]

    def update_ia(self, action, new_state, opponent, reward):
        # QTable update
        # Q(s, a) <- Q(s, a) + learning_rate * [reward + discount_factor * max(qtable[a]) - Q(s, a)]
        maxQ = 0.0
        # max of qtable
        for a in ACTIONS:
            if opponent.last_action is not None:
                if self.__qtable[new_state][a][opponent.state][opponent.last_action] > maxQ:
                    maxQ = self.__qtable[new_state][a][opponent.state][opponent.last_action]
        LEARNING_RATE = 0.8
        DISCOUNT_FACTOR = 0.8

        if opponent.last_action is not None:
            self.__qtable[self.__state][action][opponent.state][opponent.last_action] += \
                LEARNING_RATE * (reward + DISCOUNT_FACTOR * maxQ -
                                 self.__qtable[self.__state][action][opponent.state][opponent.last_action])

        self.__state = new_state
        self.__score += reward
        self.__last_action = self.actual_action
        self.__actual_action = None

    # Best action who maximise reward
    def best_action(self, opponent):
        possible_rewards = self.__qtable[self.__state]
        best = None
        if random() < self.__exploration:
            best = choice(list(possible_rewards.keys()))
            self.__exploration *= 0.99
        for a in possible_rewards:
            if opponent.last_action is None:
                if best is None or possible_rewards[a][opponent.state][a] > possible_rewards[best][opponent.state][a]:
                    best = a
            else:
                if best is None or possible_rewards[a][opponent.state][opponent.last_action] > \
                        possible_rewards[best][opponent.state][opponent.last_action]:
                    best = a
        self.__actual_action = best

    def attack(self, new_state, target):
        reward = 0
        self.__is_attacking = True
        arcade.play_sound(ATTACK_SOUND)
        if self.get_distance_between_players(new_state, target.state) == 1:
            if target.actual_action != BLOCK:
                target.__is_touched = True
                target.__health -= 1
                arcade.play_sound(HIT_SOUND)
                reward += REWARD_WOUND_TARGET
            else:
                target.__is_blocking = True
                arcade.play_sound(BLOCK_SOUND)
                reward = REWARD_TOUCH_BLOCKING_TARGET
        else:
            reward = REWARD_TOUCH_EMPTY
        return reward

    def get_distance_between_players(self, state_agent1, state_agent2):
        return abs(state_agent1[0] - state_agent2[0]) + abs(state_agent1[1] - state_agent2[1])

    def update_animation(self, delta_time: float = 1 / 60):

        # Figure out if we need to flip face left or right
        if self.__change_x < 0 and self.character_face_direction == RIGHT_FACING:
            self.character_face_direction = LEFT_FACING
        elif self.__change_x > 0 and self.character_face_direction == LEFT_FACING:
            self.character_face_direction = RIGHT_FACING

        # Jumping animation
        if self.__change_y > 0 and not self.__is_on_ladder:
            self.texture = self.jump_texture_pair[self.character_face_direction]
            return
        elif self.__change_y < 0 and not self.__is_on_ladder:
            self.texture = self.fall_texture_pair[self.character_face_direction]
            return

        # Block animation
        if self.__is_blocking:
            self.texture = self.block_texture_pair[self.character_face_direction]
            return

        # Attacking animation
        if self.__is_attacking and self.__change_x == 0:
            self.__cur_attack_texture = 0
            self.__cur_attack_texture += 1
            if self.__cur_attack_texture > 8:
                self.__cur_attack_texture = 0
                self.__is_attacking = False
            self.texture = self.attack_textures[self.__cur_attack_texture][
                self.character_face_direction
            ]
            return
        elif not self.__is_alive and not self.__is_down and self.__change_x == 0:
            self.__cur_dead_texture += 1
            if self.__cur_dead_texture > 10:
                self.__is_down = True
            self.texture = self.dead_textures[self.__cur_dead_texture][
                self.character_face_direction
            ]
            return
        # Idle animation
        elif self.__change_x == 0 and self.__is_alive:
            self.__cur_idle_texture += 1
            if self.__cur_idle_texture > 14:
                self.__cur_idle_texture = 0
            self.texture = self.idle_textures[self.__cur_idle_texture][
                self.character_face_direction
            ]
            return

        # Walking animation
        if not self.__is_down:
            self.__cur_texture += 1
            if self.__cur_texture > 7:
                self.__cur_texture = 0
            self.texture = self.walk_textures[self.__cur_texture][
                self.character_face_direction
            ]

    def save_qtable(self, file_name):
        with open(file_name + '.dat', 'wb') as f:
            pickle.dump(self.qtable, f)

    def load_qtable(self, file_name):
        with open(file_name + '.dat', 'rb') as f:
            self.qtable = pickle.load(f)

    @property
    def score(self):
        return self.__score

    def _get_qtable(self):
        return self.__qtable

    def _set_qtable(self, qtable):
        self.__qtable = qtable

    def _get_agent_number(self):
        return self.__agent_number

    def _set_agent_number(self, agent_number):
        self.__agent_number = agent_number

    agent_number = property(_get_agent_number, _set_agent_number)

    qtable = property(_get_qtable, _set_qtable)

    def reset(self, environment):
        self.__state = environment.start

    @property
    def last_action(self):
        return self.__last_action

    def _get_health(self):
        return self.__health

    def _set_health(self, health):
        self.__health = health

    health = property(_get_health, _set_health)

    def _get_is_alive(self):
        return self.__is_alive

    def _set_is_alive(self, is_alive):
        self.__is_alive = is_alive

    is_alive = property(_get_is_alive, _set_is_alive)

    def _get_health_bar(self):
        return self.__health_bar

    def _set_health_bar(self, health_bar):
        self.__health_bar = health_bar

    health_bar = property(_get_health_bar, _set_health_bar)

    def _get_state(self):
        return self.__state

    def _get_is_touched(self):
        return self.__is_touched

    def _set_is_touched(self, is_touched):
        self.__is_touched = is_touched

    is_touched = property(_get_is_touched, _set_is_touched)

    def _set_state(self, state):
        self.__state = state

    state = property(_get_state, _set_state)

    def _get_actual_action(self):
        return self.__actual_action

    def _set_actual_action(self, actual_action):
        self.__actual_action = actual_action

    actual_action = property(_get_actual_action, _set_actual_action)

