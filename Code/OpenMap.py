import os
import arcade

# --- Constantes ---
SCREEN_WIDTH = 640
SCREEN_HEIGHT = 480
SCREEN_TITLE = "Plateforme 2D avec map fixe"

TILE_SCALING = 1.48

#MAP_FILE = ".\\..\\Tileset\\Maps\\First_Map.tmx"  # N°3
MAP_FILE = "../assets/Tileset\\Maps\\Second_Map.tmx"
#MAP_FILE = ".\\..\\Tileset\\Maps\\Last_Map.tmx"

PLAYER_MOVEMENT_SPEED = 5
PLAYER_JUMP_SPEED = 15
GRAVITY = 1

IDLE_FOLDER = ".\\..\\assets\\sprites\\Monster_1\\idle"
WALK_FOLDER = ".\\..\\assets\\sprites\\Monster_1\\walk"

FRAME_TIME = 0.12

print(MAP_FILE)

class MyGame(arcade.Window):
    def __init__(self):
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)

        self.tile_map = None
        self.player_list = None
        self.player_sprite = None
        self.physics_engine = None

        # Animation
        self.idle_textures = []
        self.walk_textures = []
        self.current_textures = []  # idle ou walk
        self.current_frame = 0
        self.frame_timer = 0

    def setup(self):
        arcade.set_background_color(arcade.color.AZURE)

        # --- Charger la map ---
        self.tile_map = arcade.load_tilemap(MAP_FILE, scaling=TILE_SCALING)

        # --- Charger les textures ---
        self.idle_textures = [
            arcade.load_texture(os.path.join(IDLE_FOLDER, f))
            for f in sorted(os.listdir(IDLE_FOLDER))
            if f.startswith("Monster_1_idle_") and f.endswith(".png")
        ]
        self.walk_textures = [
            arcade.load_texture(os.path.join(WALK_FOLDER, f))
            for f in sorted(os.listdir(WALK_FOLDER))
            if f.startswith("Monster_1_walk_") and f.endswith(".png")
        ]

        # Créer joueur
        self.player_list = arcade.SpriteList()
        self.player_sprite = arcade.Sprite()
        self.player_sprite.texture = self.idle_textures[0]
        self.player_sprite.center_x = 100
        self.player_sprite.center_y = 400
        self.player_sprite.scale = 1
        self.player_list.append(self.player_sprite)

        # --- Définition du sol ---
        wall_list = self.tile_map.sprite_lists["Ground"]
        self.physics_engine = arcade.PhysicsEnginePlatformer(
            self.player_sprite, wall_list, gravity_constant=GRAVITY
        )

        # Animation par défaut = idle
        self.current_textures = self.idle_textures

    def on_draw(self):
        self.clear()

        # Dessiner les calques
        if self.tile_map:
            for layer in self.tile_map.sprite_lists.values():
                layer.draw()
        self.player_list.draw()

    def on_update(self, delta_time):
        self.physics_engine.update()

        # Choix de l'animation
        if self.player_sprite.change_x == 0:
            self.current_textures = self.idle_textures
        else:
            self.current_textures = self.walk_textures

        # Mise à jour de l'image selon le temps
        self.frame_timer += delta_time
        if self.frame_timer > FRAME_TIME:
            self.frame_timer = 0
            self.current_frame = (self.current_frame + 1) % len(self.current_textures)
            self.player_sprite.texture = self.current_textures[self.current_frame]

    def on_key_press(self, key, modifiers):
        if key in (arcade.key.UP, arcade.key.SPACE):
            if self.physics_engine.can_jump():
                self.player_sprite.change_y = PLAYER_JUMP_SPEED
        elif key == arcade.key.LEFT:
            self.player_sprite.change_x = -PLAYER_MOVEMENT_SPEED
        elif key == arcade.key.RIGHT:
            self.player_sprite.change_x = PLAYER_MOVEMENT_SPEED

    def on_key_release(self, key, modifiers):
        if key in (arcade.key.LEFT, arcade.key.RIGHT):
            self.player_sprite.change_x = 0


if __name__ == "__main__":
    game = MyGame()
    game.setup()
    arcade.run()
