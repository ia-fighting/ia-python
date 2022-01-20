# Game environment class
import os

import arcade
import matplotlib.pyplot as plt
from arcade.gui import UIManager

from AgentManager import AgentManager
from GameEnvironement import *


AMBIANCE_SOUND = arcade.load_sound(f"{SOUNDS_PATH}/ambiance.mp3")


def display_plot():
    """
    Display a plot of data
    """
    # print(SCORE_TABLES_EVOLUTIONS)

    X = PLT_GENERATION_NUMBER

    # Assign variables to the y axis part of the curve
    y = SCORE_TABLES_EVOLUTIONS[0]
    z = SCORE_TABLES_EVOLUTIONS[1]

    # print(y)
    # print(z)
    # print(X)

    # Plotting both the curves simultaneously
    plt.plot(X, y, color='r', label='Agent 1')
    plt.plot(X, z, color='g', label='Agent 2')

    # Naming the x-axis, y-axis and the whole graph
    plt.xlabel("Generations")
    plt.ylabel("Scores")
    plt.title("Evolution of the scores by agents")

    # Adding legend, which helps us recognize the curve according to it's color
    plt.legend()

    # To load the display window
    plt.show()


class MyGame(arcade.Window):
    """
    Main application class.
    """

    def __init__(self):

        # Call the parent class and set up the window
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)

        # Our Scene Object
        self.ia_env = GameEnvironment(ARENA)
        # initialize AgentManager
        self.ia_am = AgentManager(self.ia_env, 2, MAX_HP)

        SCORE_TABLES_EVOLUTIONS[0] = []
        SCORE_TABLES_EVOLUTIONS[1] = []
        self.scene = None

        # Initialize  Ui Manager
        self.ui_manager = UIManager()
        self.ui_manager.enable()

        # Background image will be stored in this variable
        self.background = None

        self.active_ambiance = True

        # Separate variable that holds the players sprite
        self.player_one_sprite = None
        self.player_two_sprite = None

        self.game_over = None
        # Our physics engine
        self.physics_engine = None
        self.wall_list = None
        self.music_toggle_button = None
        self.ambiance_player = arcade.play_sound(AMBIANCE_SOUND, 0.8, 0.0, True)
        self.__generation_counter = 0
        self.__iteration_counter = 0

    def setup(self):
        """Set up the game here. Call this function to restart the game."""

        # Initialize Scene
        self.scene = arcade.Scene()
        self.bone = None

        self.background = arcade.load_texture(f"{SPRITES_PATH}/BG.png")

        # retrieve first agent of the ia_am
        self.player_one_sprite = self.ia_am.agents[0]
        self.player_one_sprite.center_x = self.player_one_sprite.state[1] * PLAYER_START_X
        self.player_one_sprite.center_y = PLAYER_ONE_START_Y
        self.scene.add_sprite(LAYER_NAME_PLAYER_ONE, self.player_one_sprite)

        # Set up the player two, specifically placing it at these coordinates.
        self.player_two_sprite = self.ia_am.agents[1]
        self.player_two_sprite.center_x = self.player_two_sprite.state[1] * PLAYER_START_X
        self.player_two_sprite.center_y = PLAYER_TWO_START_Y
        self.scene.add_sprite(LAYER_NAME_PLAYER_TWO, self.player_two_sprite)

        self.wall_list = arcade.SpriteList(use_spatial_hash=True)

        # This shows using a loop to place multiple sprites horizontally
        tile_source = f"{SPRITES_PATH}/tiles/tile2.png"
        for x in range(0, 1250, 64):
            wall = arcade.Sprite(tile_source, 1)
            wall.center_x = x
            wall.center_y = 64
            self.scene.add_sprite("Walls", wall)

        coordinate_tree = [512, 304]
        tree = arcade.Sprite(f"{SPRITES_PATH}/objects/tree.png", 1.5)
        tree.position = coordinate_tree
        self.wall_list.append(tree)

        coordinate_tomb = [768, 168]
        tomb = arcade.Sprite(f"{SPRITES_PATH}/objects/tomb_stone1.png", 1.5)
        tomb.position = coordinate_tomb
        self.wall_list.append(tomb)

        coordinate_arrow = [156, 172]
        arrow = arcade.Sprite(f"{SPRITES_PATH}/objects/arrow_sign.png", 1)
        arrow.position = coordinate_arrow
        self.wall_list.append(arrow)

        coordinate_skeleton = [456, 140]
        skeleton = arcade.Sprite(f"{SPRITES_PATH}/objects/skeleton.png", 0.5)
        skeleton.position = coordinate_skeleton
        self.wall_list.append(skeleton)

        # Create the ground
        coordinate_bone = [755, 80]
        self.bone = arcade.Sprite(f"{SPRITES_PATH}/tiles/bone3.png", 0.7)
        self.bone.position = coordinate_bone

        # Create the player one preview
        coordinate_player_one_preview = [35, 590]
        player_one_preview = arcade.Sprite(f"{SPRITES_PATH}/male/preview.png", 0.2)
        player_one_preview.position = coordinate_player_one_preview
        self.wall_list.append(player_one_preview)

        # Create the player one preview
        coordinate_player_two_preview = [965, 590]
        player_two_preview = arcade.Sprite(f"{SPRITES_PATH}/female/preview.png", 0.2)
        player_two_preview.position = coordinate_player_two_preview
        self.wall_list.append(player_two_preview)

        for i in range(1, self.player_one_sprite.health + 1):
            coordinate_heart = [60 + i * 30, 600]
            heart = arcade.Sprite(f"{SPRITES_PATH}/objects/heart.png", 0.05)
            heart.position = coordinate_heart
            self.player_one_sprite.health_bar.append(heart)

        for i in range(1, self.player_two_sprite.health + 1):
            coordinate_heart = [940 - i * 30, 600]
            heart = arcade.Sprite(f"{SPRITES_PATH}/objects/heart.png", 0.05)
            heart.position = coordinate_heart
            self.player_two_sprite.health_bar.append(heart)

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
            texture=arcade.load_texture(f"{SPRITES_PATH}/objects/game_over.png", 0.5),
        )

        self.music_toggle_button.on_click = self.toggle_music
        self.ui_manager.add(self.music_toggle_button)

        # Create the 'physics engine'
        self.player_one_physics_engine = arcade.PhysicsEnginePlatformer(
            self.player_one_sprite, gravity_constant=GRAVITY, walls=self.scene["Walls"]
        )

        self.player_two_physics_engine = arcade.PhysicsEnginePlatformer(
            self.player_two_sprite, gravity_constant=GRAVITY, walls=self.scene["Walls"]
        )

    def on_key_press(self, key, modifiers):
        """Called whenever a key is pressed."""
        # Gui
        if key == arcade.key.M:
            self.toggle_music(event=None)

        # Player One Actions
        if key == arcade.key.R:
            self.ia_am.reset()
            self.setup()

        if key == arcade.key.I:
            self.load_qtable(self.ia_am.agents, "I")
        if key == arcade.key.NUM_0:
            self.load_qtable(self.ia_am.agents, "0")
        if key == arcade.key.NUM_1:
            self.load_qtable(self.ia_am.agents, "1")
        if key == arcade.key.NUM_2:
            self.load_qtable(self.ia_am.agents, "2")

        if key == arcade.key.P:
            self.ia_am.player_1_priority = not self.ia_am.player_1_priority

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
        self.player_one_sprite.health_bar.draw()
        self.player_two_sprite.health_bar.draw()

        # Draw our Scene
        self.scene.draw()
        self.bone.draw()
        self.ui_manager.draw()

        self.draw_text()

    def draw_text(self):
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

        # Draw game iterations
        game_iterations = f"Iteration: {self.__iteration_counter}"
        arcade.draw_text(
            game_iterations,
            30,
            30,
            arcade.csscolor.WHITE,
            14,
            bold=True
        )

        # Draw game iterations
        game_generation = f"Generation: {self.__generation_counter}"
        arcade.draw_text(
            game_generation,
            30,
            10,
            arcade.csscolor.WHITE,
            14,
            bold=True
        )

    def on_update(self, delta_time):
        """Movement and game logic"""
        # Remove heart
        self.player_one_sprite = self.ia_am.agents[0]
        self.player_two_sprite = self.ia_am.agents[1]

        self.update_health_bar(self.player_one_sprite)
        self.update_health_bar(self.player_two_sprite)

        self.player_one_sprite.center_x = self.player_one_sprite.state[1] * PLAYER_START_X
        self.player_one_sprite.center_y = PLAYER_ONE_START_Y

        # Set up the player two, specifically placing it at these coordinates.
        self.player_two_sprite.center_x = self.player_two_sprite.state[1] * PLAYER_START_X
        self.player_two_sprite.center_y = PLAYER_TWO_START_Y

        # Move the player with the physics engine
        self.player_one_physics_engine.update()
        self.player_two_physics_engine.update()

        # Update Animations
        self.scene.update_animation(
            delta_time, [LAYER_NAME_PLAYER_ONE, LAYER_NAME_PLAYER_TWO]
        )

        if not self.ia_am.goal:
            self.ia_am.best_actions()
            self.ia_am.apply_actions(self.ia_am.get_alive_agents)
            self.update_action_animation(True, self.player_one_sprite)
            self.update_action_animation(True, self.player_two_sprite)
            self.__iteration_counter += 1
            self.update_action_animation(False, self.player_one_sprite)
            self.update_action_animation(False, self.player_two_sprite)
        else:
            PLT_GENERATION_NUMBER.append(self.__generation_counter)
            for i in range(len(self.ia_am.agents)):
                SCORE_TABLES_EVOLUTIONS[i].append(self.ia_am.agents[i].score)
            self.ia_am.reset()
            self.setup()
            self.__generation_counter += 1
            if self.__generation_counter % 2 == 0:
                self.save_qtables(self.ia_am.agents)
            self.__iteration_counter = 0

        self.scene.update_animation(
            delta_time, [LAYER_NAME_PLAYER_ONE, LAYER_NAME_PLAYER_TWO]
        )

    def save_qtables(self, agents):
        for i in range(len(agents)):
            agents[i].save_qtable(f"../qtable_agent_{i}")

    def load_qtable(self, agents, key):
        if(key == "I"):
            for i in range(len(agents)):
                agents[i].load_qtable('../qtable_agent_' + str((agents[i].agent_number + 1) % 2))
        if(key == "0"):
            for i in range(len(agents)):
                agents[i].load_qtable('../qtable_agent_' + str(agents[i].agent_number))
        if (key == "1"):
            for i in range(len(agents)):
                agents[i].load_qtable('../qtable_agent_' + str(agents[0].agent_number))
        if (key == "0"):
            for i in range(len(agents)):
                agents[i].load_qtable('../qtable_agent_' + str(agents[1].agent_number))

    def update_health_bar(self, player_sprite):
        if MAX_HP > player_sprite.health >= 0 and player_sprite.is_touched:
            if len(player_sprite.health_bar) > 0:
                player_sprite.is_touched = False
                player_sprite.health_bar.pop()
                player_sprite.health_bar.draw()

    def update_action_animation(self, is_beginning, player_sprite):
        if is_beginning:
            if player_sprite.last_action == LEFT and self.player_one_sprite.is_alive:
                player_sprite.__change_x = -PLAYER_MOVEMENT_SPEED
                player_sprite.__is_walking = True
                player_sprite.character_face_direction = LEFT_FACING
            elif player_sprite.last_action == RIGHT and self.player_one_sprite.is_alive:
                player_sprite.__is_walking = True
                player_sprite.__change_x = PLAYER_MOVEMENT_SPEED
                player_sprite.character_face_direction = RIGHT_FACING
            elif player_sprite.last_action == BLOCK and player_sprite.is_alive:
                player_sprite.__is_blocking = True
        else:
            if player_sprite.last_action == LEFT:
                player_sprite.__change_x = 0
                player_sprite.__is_walking = False
            elif player_sprite.last_action == RIGHT:
                player_sprite.__change_x = 0
                player_sprite.__is_walking = False
            elif player_sprite.last_action == PUNCH:
                player_sprite.__change_x = 0
                player_sprite.__is_attacking = False
            elif player_sprite.last_action == BLOCK:
                player_sprite.__is_blocking = False


def main():
    """Main function"""
    window = MyGame()
    window.setup()
    arcade.run()


if __name__ == "__main__":
    main()
    display_plot()
