# Game environment class
import time

import pyautogui

from utils.Singleton import Singleton
import os
import arcade
from PIL.Image import Image
from arcade.gui import UIManager

ARENA = """##*      *##"""

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

PLAYER_1 = {RIGHT: 'D', LEFT: 'Q', PUNCH:'A', BLOCK:'E'}
PLAYER_2 = {RIGHT: 'L', LEFT: 'J', PUNCH:'U', BLOCK:'O'}

ARCADE_KEYS = {'A': 97, 'B': 98, 'C': 99, 'D': 100, 'E': 101, 'F': 102, 'G': 103, 'H': 104, 'I': 105, 'J': 106, 'K': 107, 'L': 108, 'M': 109, 'N': 110, 'O': 111, 'P': 112, 'Q': 113, 'R': 114, 'S': 115, 'T': 116, 'U': 117, 'V': 118, 'W': 119, 'X': 120, 'Y': 121, 'Z': 122}
"""
Platformer Game
"""

SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 650
SCREEN_TITLE = "ZOMBIE FIGHTING"

# Constants used to scale our sprites from their original size
TILE_SCALING = 0.5
CHARACTER_SCALING = 0.3
SPRITE_PIXEL_SIZE = 128
GRID_PIXEL_SIZE = SPRITE_PIXEL_SIZE * TILE_SCALING

# Movement speed of player, in pixels per frame
PLAYER_MOVEMENT_SPEED = 7
GRAVITY = 2
PLAYER_JUMP_SPEED = 30

PLAYER_ONE_START_X = SPRITE_PIXEL_SIZE * TILE_SCALING * 5
PLAYER_ONE_START_Y = SPRITE_PIXEL_SIZE * TILE_SCALING * 3

PLAYER_TWO_START_X = SPRITE_PIXEL_SIZE * TILE_SCALING * 10
PLAYER_TWO_START_Y = SPRITE_PIXEL_SIZE * TILE_SCALING * 3

MAX_HP = 10

# Constants used to track if the player is facing left or right
RIGHT_FACING = 0
LEFT_FACING = 1

LAYER_NAME_LADDERS = "Ladders"
LAYER_NAME_PLAYER_ONE = "PlayerOne"
LAYER_NAME_PLAYER_TWO = "PlayerTwo"


def load_texture_pair(filename):
    """
    Load a texture pair, with the second being a mirror image.
    """
    return [
        arcade.load_texture(filename),
        arcade.load_texture(filename, flipped_horizontally=True),
    ]

class PlayerCharacter(arcade.Sprite):
    """Player Sprite"""

    def __init__(self, sprites, face_direction):

        # Set up parent class
        super().__init__()

        # Default to face-right
        self.character_face_direction = face_direction

        self.hp = MAX_HP
        self.score = 0

        # Used for flipping between image sequences
        self.cur_texture = 0
        self.cur_attack_texture = 0
        self.cur_idle_texture = 0
        self.cur_dead_texture = 0
        self.scale = CHARACTER_SCALING

        # Track our state
        self.is_on_ladder = False
        self.attacking = False
        self.touched = False
        self.blocking = False
        self.is_dead = False
        self.is_alive = True
        self.is_down = False

        # --- Load Textures ---
        main_path = f"./asset/sprites/png/{sprites}"

        # Load textures for idle standing
        self.idle_texture_pair = load_texture_pair(f"{main_path}/Idle1.png")
        self.jump_texture_pair = load_texture_pair(f"{main_path}/Dead3.png")
        self.fall_texture_pair = load_texture_pair(f"{main_path}/Idle1.png")
        self.block_texture_pair = load_texture_pair(f"{main_path}/Dead1.png")

        # Load textures for walking
        self.walk_textures = []
        for i in range(1, 10):
            walk_texture = load_texture_pair(f"{main_path}/Walk{i}.png")
            self.walk_textures.append(walk_texture)

        # Load textures for attacking
        self.attack_textures = []
        for i in range(1, 8):
            attack_texture = load_texture_pair(f"{main_path}/Attack{i}.png")
            self.attack_textures.append(attack_texture)

        self.idle_textures = []
        for i in range(1, 16):
            idle_texture = load_texture_pair(f"{main_path}/Idle{i}.png")
            self.idle_textures.append(idle_texture)

        self.dead_textures = []
        for i in range(1, 13):
            dead_texture = load_texture_pair(f"{main_path}/Dead{i}.png")
            self.dead_textures.append(dead_texture)

        # Set the initial texture
        if not self.attacking:
            self.texture = self.idle_texture_pair[0]

    def attack(self, target, attack_sound, hit_sound, block_sound):
        arcade.play_sound(attack_sound)
        self.attacking = True
        if arcade.get_distance_between_sprites(self, target) < 65:
            if target.blocking:
                arcade.play_sound(block_sound)
            else:
                target.touched = True
                target.hp -= 1
                arcade.play_sound(hit_sound)

            # Todo remove
            self.score += 1

        if target.hp <=0:
            target.is_alive = False

    def update_animation(self, delta_time: float = 1 / 60):

        # Figure out if we need to flip face left or right
        if self.change_x < 0 and self.character_face_direction == RIGHT_FACING:
            self.character_face_direction = LEFT_FACING
        elif self.change_x > 0 and self.character_face_direction == LEFT_FACING:
            self.character_face_direction = RIGHT_FACING

        # Jumping animation
        if self.change_y > 0 and not self.is_on_ladder:
            self.texture = self.jump_texture_pair[self.character_face_direction]
            return
        elif self.change_y < 0 and not self.is_on_ladder:
            self.texture = self.fall_texture_pair[self.character_face_direction]
            return

        # Block animation
        if self.blocking == True:
            self.texture = self.block_texture_pair[self.character_face_direction]
            return

        # Attacking animation
        if self.attacking and self.change_x == 0:
            self.cur_attack_texture = 0
            self.cur_attack_texture += 1
            if self.cur_attack_texture > 8:
                self.cur_attack_texture = 0
                self.attacking = False
            self.texture = self.attack_textures[self.cur_attack_texture][
                self.character_face_direction
            ]
            return
        elif not self.is_alive and not self.is_down and self.change_x == 0:
            self.cur_dead_texture += 1
            if self.cur_dead_texture > 10:
                self.is_down = True
            self.texture = self.dead_textures[self.cur_dead_texture][
                self.character_face_direction
            ]
            return
        # Idle animation
        elif self.change_x == 0 and self.is_alive:
            self.cur_idle_texture += 1
            if self.cur_idle_texture > 14:
                self.cur_idle_texture = 0
            self.texture = self.idle_textures[self.cur_idle_texture][
                self.character_face_direction
            ]
            return


        # Walking animation
        if not self.is_down:
            self.cur_texture += 1
            if self.cur_texture > 7:
                self.cur_texture = 0
            self.texture = self.walk_textures[self.cur_texture][
                self.character_face_direction
            ]


class MyGame(arcade.Window):
    """
    Main application class.
    """

    def __init__(self):

        # Call the parent class and set up the window
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)

        # Our Scene Object
        self.ia_am = None
        self.ia_env = None
        self.scene = None

        # Initialize  Ui Manager
        self.ui_manager = UIManager()
        self.ui_manager.enable()

        # Background image will be stored in this variable
        self.background = None

        self.active_ambiance = True
        self.ambiance_player = None

        # Separate variable that holds the players sprite
        self.player_one_sprite = None
        self.player_two_sprite = None

        #
        self.player_one_health_bar = None
        self.player_two_health_bar = None

        self.game_over = None

        # Our physics engine
        self.physics_engine = None

        self.wall_list = None

        self.music_toggle_button = None

        # Load sounds
        sounds_path = "./asset/sounds/"
        self.jump_sound = arcade.load_sound(f"{sounds_path}/jump.mp3")
        self.attack_sound = arcade.load_sound(f"{sounds_path}/attack_short.mp3")
        self.ambiance = arcade.load_sound(f"{sounds_path}/ambiance.mp3")
        self.block_sound = arcade.load_sound(f"{sounds_path}/block.mp3")
        self.hit_sound = arcade.load_sound(f"{sounds_path}/hit.mp3")

    def run_ia(self):
        for i in range(30):
            print('GEN: ', i)

            iteration = 0

            print('GEN: ', i, ' - ', iteration, ' iterations')

    def setup(self):
        """Set up the game here. Call this function to restart the game."""

        # Initialize Scene
        self.scene = arcade.Scene()

        self.bone = None

        self.ambiance_player = arcade.play_sound(self.ambiance, 0.8, 0.0, True)

        sprites_path = "./asset/sprites/png/"
        # Load the background image. Do this in the setup so we don't keep reloading it all the time.
        # Image from:
        # https://wallpaper-gallery.net/single/free-background-images/free-background-images-22.html
        self.background = arcade.load_texture(f"{sprites_path}/BG.png")

        # Set up the player one, specifically placing it at these coordinates.
        self.player_one_sprite = PlayerCharacter('male', RIGHT_FACING)
        self.player_one_sprite.center_x = PLAYER_ONE_START_X
        self.player_one_sprite.center_y = PLAYER_ONE_START_Y
        self.scene.add_sprite(LAYER_NAME_PLAYER_ONE, self.player_one_sprite)

        self.wall_list = arcade.SpriteList(use_spatial_hash=True)
        self.player_one_health_bar = arcade.SpriteList(use_spatial_hash=True)
        self.player_two_health_bar = arcade.SpriteList(use_spatial_hash=True)

        # Set up the player two, specifically placing it at these coordinates.
        self.player_two_sprite = PlayerCharacter('female', LEFT_FACING)
        self.player_two_sprite.center_x = PLAYER_TWO_START_X
        self.player_two_sprite.center_y = PLAYER_TWO_START_Y
        self.scene.add_sprite(LAYER_NAME_PLAYER_TWO, self.player_two_sprite)

        # This shows using a loop to place multiple sprites horizontally
        tile_source = f"{sprites_path}/tiles/tile2.png"
        for x in range(0, 1250, 64):
            wall = arcade.Sprite(tile_source, 1)
            wall.center_x = x
            wall.center_y = 64
            self.scene.add_sprite("Walls", wall)

        coordinate_tree = [512, 304]
        tree = arcade.Sprite(f"{sprites_path}/objects/tree.png", 1.5)
        tree.position = coordinate_tree
        self.wall_list.append(tree)

        coordinate_tomb = [768, 168]
        tomb = arcade.Sprite(f"{sprites_path}/objects/tomb_stone1.png", 1.5)
        tomb.position = coordinate_tomb
        self.wall_list.append(tomb)

        coordinate_arrow = [156, 172]
        arrow = arcade.Sprite(f"{sprites_path}/objects/arrow_sign.png", 1)
        arrow.position = coordinate_arrow
        self.wall_list.append(arrow)

        coordinate_skeleton = [456, 140]
        skeleton = arcade.Sprite(f"{sprites_path}/objects/skeleton.png", 0.5)
        skeleton.position = coordinate_skeleton
        self.wall_list.append(skeleton)

        # Create the ground
        coordinate_bone = [755, 80]
        self.bone = arcade.Sprite(f"{sprites_path}/tiles/bone3.png", 0.7)
        self.bone.position = coordinate_bone

        # Create the player one preview
        coordinate_player_one_preview = [35, 590]
        player_one_preview = arcade.Sprite(f"{sprites_path}/male/preview.png", 0.2)
        player_one_preview.position = coordinate_player_one_preview
        self.wall_list.append(player_one_preview)

        # Create the player one preview
        coordinate_player_two_preview = [965, 590]
        player_two_preview = arcade.Sprite(f"{sprites_path}/female/preview.png", 0.2)
        player_two_preview.position = coordinate_player_two_preview
        self.wall_list.append(player_two_preview)

        for i in range(1, self.player_one_sprite.hp + 1):
            coordinate_heart = [60 + i * 30, 600]
            heart = arcade.Sprite(f"{sprites_path}/objects/heart.png", 0.05)
            heart.position = coordinate_heart
            self.player_one_health_bar.append(heart)

        for i in range(1, self.player_two_sprite.hp + 1):
            coordinate_heart = [940 - i * 30, 600]
            heart = arcade.Sprite(f"{sprites_path}/objects/heart.png", 0.05)
            heart.position = coordinate_heart
            self.player_two_health_bar.append(heart)

        self.music_toggle_button = arcade.gui.UITextureButton(
            x=930,
            y=20,
            texture=arcade.load_texture(':resources:onscreen_controls/shaded_dark/music_on.png'),
            texture_hovered=arcade.load_texture(':resources:onscreen_controls/shaded_dark/music_off.png'),
            texture_pressed=arcade.load_texture(':resources:onscreen_controls/shaded_dark/music_off.png'),
        )

        self.game_over = arcade.gui.UITextureButton(
            x=400,
            y=500,
            texture=arcade.load_texture(f"{sprites_path}/objects/game_over.png", 0.5),
        )

        # self.game_over = arcade.gui.UITextArea(
        #     x=400,
        #     y=500,
        #     text="Game Over",
        #     font_name="Blackadder ITC",
        #     font_size=30,
        #     text_color=arcade.color.RED
        # )

        self.music_toggle_button.on_click = self.toggle_music
        self.ui_manager.add(self.music_toggle_button)

        # Create the 'physics engine'
        self.player_one_physics_engine = arcade.PhysicsEnginePlatformer(
            self.player_one_sprite, gravity_constant=GRAVITY, walls=self.scene["Walls"]
        )

        self.player_two_physics_engine = arcade.PhysicsEnginePlatformer(
            self.player_two_sprite, gravity_constant=GRAVITY, walls=self.scene["Walls"]
        )

        self.ia_env = GameEnvironment(ARENA)
        # initialize AgentManager
        self.ia_am = AgentManager(self.ia_env, 2, 80)
        self.ia_am.reset()

    def toggle_music(self, event):
        if self.active_ambiance:
            arcade.Sound.set_volume(self=self, volume=0, player=self.ambiance_player)
            self.music_toggle_button.texture = arcade.load_texture(
                ':resources:onscreen_controls/shaded_dark/music_off.png')
            self.active_ambiance = False
        else:
            arcade.Sound.set_volume(self=self, volume=1, player=self.ambiance_player)
            self.music_toggle_button.texture = arcade.load_texture(
                ':resources:onscreen_controls/shaded_dark/music_on.png')
            self.active_ambiance = True

    def on_draw(self):
        """Render the screen."""

        # Clear the screen to the background color
        arcade.start_render()

        # Draw the background texture
        arcade.draw_lrwh_rectangle_textured(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, self.background)

        # Draw all stripes
        self.wall_list.draw()
        self.player_one_health_bar.draw()
        self.player_two_health_bar.draw()

        # Draw our Scene
        self.scene.draw()
        self.bone.draw()
        self.ui_manager.draw()

        # Draw player scores
        player_one_score = f"Score: {self.player_one_sprite.score}"
        arcade.draw_text(
            player_one_score,
            30,
            550,
            arcade.csscolor.WHITE,
            14,
            bold=True
        )

        # Draw player scores
        player_two_score = f"Score: {self.player_two_sprite.score}"
        arcade.draw_text(
            player_two_score,
            885,
            550,
            arcade.csscolor.WHITE,
            14,
            bold=True
        )


        # Hit_box
        # self.player_two_sprite.draw_hit_box(arcade.color.RED)
        # self.player_one_sprite.draw_hit_box(arcade.color.YELLOW)

    def on_key_press(self, key, modifiers):
        """Called whenever a key is pressed."""
        # Gui
        if key == arcade.key.M:
            self.toggle_music(event=None)

        # Player One Actions
        if key == arcade.key.Z and self.player_one_sprite.is_alive:
            if self.player_one_physics_engine.can_jump():
                self.player_one_sprite.change_y = PLAYER_JUMP_SPEED
                arcade.play_sound(self.jump_sound)
        elif key == arcade.key.Q and self.player_one_sprite.is_alive:
            self.player_one_sprite.change_x = -PLAYER_MOVEMENT_SPEED
        elif key == arcade.key.D and self.player_one_sprite.is_alive:
            self.player_one_sprite.change_x = PLAYER_MOVEMENT_SPEED
        elif key == arcade.key.A and self.player_one_sprite.is_alive:
            self.player_one_sprite.attack(self.player_two_sprite, self.attack_sound, self.hit_sound, self.block_sound)
        elif key == arcade.key.E and self.player_one_sprite.is_alive:
            self.player_one_sprite.blocking = True

        # Player TWO Actions
        if key == arcade.key.I and self.player_two_sprite.is_alive:
            if self.player_two_physics_engine.can_jump():
                self.player_two_sprite.change_y = PLAYER_JUMP_SPEED
                arcade.play_sound(self.jump_sound)
        elif key == arcade.key.J and self.player_two_sprite.is_alive:
            self.player_two_sprite.change_x = -PLAYER_MOVEMENT_SPEED
        elif key == arcade.key.L and self.player_two_sprite.is_alive:
            self.player_two_sprite.change_x = PLAYER_MOVEMENT_SPEED
        elif key == arcade.key.U and self.player_two_sprite.is_alive:
            self.player_two_sprite.attack(self.player_one_sprite, self.attack_sound, self.hit_sound, self.block_sound)
        elif key == arcade.key.O and self.player_two_sprite.is_alive:
            self.player_two_sprite.blocking = True

    def on_key_release(self, key, modifiers):
        """Called when the user releases a key."""

        if key == arcade.key.LEFT or key == arcade.key.Q:
            self.player_one_sprite.change_x = 0
        elif key == arcade.key.RIGHT or key == arcade.key.D:
            self.player_one_sprite.change_x = 0
        elif key == arcade.key.A:
            self.player_one_sprite.change_x = 0
            self.player_one_sprite.attacking = False
        elif key == arcade.key.E:
            self.player_one_sprite.blocking = False

        if key == arcade.key.J:
            self.player_two_sprite.change_x = 0
        elif key == arcade.key.L:
            self.player_two_sprite.change_x = 0
        elif key == arcade.key.U:
            self.player_two_sprite.change_x = 0
            self.player_two_sprite.attacking = False
        elif key == arcade.key.O:
            self.player_two_sprite.blocking = False

    def on_update(self, delta_time):
        """Movement and game logic"""

        # Remove heart
        if MAX_HP > self.player_one_sprite.hp >= 0 and self.player_one_sprite.touched:
            self.player_one_sprite.touched = False
            self.player_one_health_bar.pop()
            self.player_one_health_bar.draw()

        if MAX_HP > self.player_two_sprite.hp >= 0 and self.player_two_sprite.touched:
            self.player_two_sprite.touched = False
            self.player_two_health_bar.pop()
            self.player_two_health_bar.draw()

        # if not self.player_one_sprite.is_alive or not self.player_two_sprite.hp:
        #     self.ui_manager.add(self.game_over)
        #     self.ui_manager.draw()


        # Move the player with the physics engine
        self.player_one_physics_engine.update()


        if not self.ia_am.goal:
            self.ia_am.best_actions()
            self.ia_am.apply_actions(self.ia_am.get_alive_agents)
            # if iteration % 1000 == 0:
            # print('iteration :', iteration)

        # Update Animations
        self.scene.update_animation(
            delta_time, [LAYER_NAME_PLAYER_ONE, LAYER_NAME_PLAYER_TWO]
        )

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
                    #print("{} has been wounded".format(agent.health))
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
            #print('Agent ', i, ' action :', agent.actual_action)
            #print('Agent ', i, ' health :', agent.health)
            if agent.is_alive():
                actual_action = agent.actual_action
                if actual_action in MOVING_ACTIONS:
                    self.__environment.apply(agents[i])
                    self.update_front(actual_action, i)
        # Apply others actions
        #print(self.__environment.get_players_state)
        #print(self.__environment.is_near_players(agents[0].state))
        for i in range(len(agents)):
            agent = agents[i]
            if agents[i].is_alive():
                actual_action = agent.actual_action
                if actual_action not in MOVING_ACTIONS and actual_action is not None:
                    self.__environment.apply(agent)
                    self.update_front(actual_action, i)

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

    def update_front(self, action, player):
        if action is not None:
            key = self.retrieve_key_font(action, player)
            print(key)
            pyautogui.press(key)

    def retrieve_key_font(self, action, player):
        if player == 0:
           return PLAYER_1[action]
        elif player == 1:
           return PLAYER_2[action]


def main():
    """Main function"""
    window = MyGame()
    window.setup()
    arcade.run()

    """for i in range(30):
        print('GEN: ', i)
        am.reset()
        iteration = 0
        while not am.goal:
            iteration += 1
            am.best_actions()
            am.apply_actions(am.get_alive_agents)
            #if iteration % 1000 == 0:
                #print('iteration :', iteration)
            if (i == 4):
                time.sleep(0.3)
                am.display(i, iteration, len(list(map(lambda x: x.strip(), ARENA.strip().split('\n')))[0]))
        print('GEN: ', i, ' - ', iteration, ' iterations')"""


if __name__ == "__main__":
    main()
