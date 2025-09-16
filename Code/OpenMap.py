import arcade

# --- Constantes ---
SCREEN_WIDTH = 640
SCREEN_HEIGHT = 480
SCREEN_TITLE = "Plateforme 2D avec map fixe"

TILE_SCALING = 1.48

# Les différentes maps de notre jeu 
MAP_FILE = ".\..\Tileset\oak_woods_v1.0\First_Map.tmx" # N°1
#MAP_FILE = ".\..\Tileset\Dungeon Tile Set\Last_Map.tmx" # N°3


class MyGame(arcade.Window):
    def __init__(self):
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)

        self.tile_map = None
        self.wall_list = None
        self.player_list = None
        self.player_sprite = None
        self.physics_engine = None

    def setup(self):
        arcade.set_background_color(arcade.color.AZURE)

        # --- Charger la map ---
        self.tile_map = arcade.load_tilemap(MAP_FILE, scaling=TILE_SCALING)

        # Récupérer les calques en SpriteList
        self.wall_list = self.tile_map.sprite_lists.get("Platforms")  # nom du calque dans Tiled
        self.player_list = arcade.SpriteList()

        # --- Créer le joueur ---
        self.player_sprite = arcade.Sprite(":resources:images/animated_characters/female_person/femalePerson_idle.png", 1.5)
        self.player_sprite.center_x = 100
        self.player_sprite.center_y = 2000
        self.player_list.append(self.player_sprite)

        # --- Moteur physique ---
        self.physics_engine = arcade.PhysicsEnginePlatformer(
            self.player_sprite, self.wall_list, gravity_constant=1
        )

    def on_draw(self):
        self.clear()

        # Dessiner les calques
        if self.tile_map:
            for layer in self.tile_map.sprite_lists.values():
                layer.draw()

        self.player_list.draw()

    def on_update(self, delta_time):
        self.physics_engine.update()

    def on_key_press(self, key, modifiers):
        if key == arcade.key.UP or key == arcade.key.SPACE:
            if self.physics_engine.can_jump():
                self.player_sprite.change_y = 20
        elif key == arcade.key.LEFT:
            self.player_sprite.change_x = -5
        elif key == arcade.key.RIGHT:
            self.player_sprite.change_x = 5

    def on_key_release(self, key, modifiers):
        if key == arcade.key.LEFT or key == arcade.key.RIGHT:
            self.player_sprite.change_x = 0


if __name__ == "__main__":
    game = MyGame()
    game.setup()
    arcade.run()
