"""
Platformer Game
"""
import arcade
from PIL.Image import Image
from arcade.gui import UIManager

# Constants
from core.GameEnvironment import GameEnvironment, AgentManager, ARENA

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
            self.ia_am.reset()
            iteration = 0
            while not self.ia_am.goal:
                iteration += 1
                self.ia_am.best_actions()
                self.ia_am.apply_actions(self.ia_am.get_alive_agents)
                # if iteration % 1000 == 0:
                # print('iteration :', iteration)
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

        self.ia_env = GameEnvironment(ARENA)
        # initialize AgentManager
        self.ia_am = AgentManager(self.ia_env, 2, 80)
        self.run_ia()

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
        self.player_two_physics_engine.update()

        # Update Animations
        self.scene.update_animation(
            delta_time, [LAYER_NAME_PLAYER_ONE, LAYER_NAME_PLAYER_TWO]
        )


def main():
    """Main function"""
    window = MyGame()
    window.setup()
    arcade.run()


if __name__ == "__main__":
    main()