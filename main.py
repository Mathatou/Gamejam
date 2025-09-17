
#--- main.py ---
import arcade
import importlib
from scene2 import Scene
# --- Constantes ---
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
SCREEN_TITLE = "Plateforme 2D avec Boss et Follower animé"

class MainWindow(arcade.Window):
    def __init__(self, width=800, height=600, title="Main"):
        super().__init__(width, height, title)
        self.current_scene = None
        self.scene_module = None
        self.background_player = None

    def setup_scene(self, scene_module_name='scene1'):
        try:
            mod = importlib.import_module(scene_module_name)
            SceneClass = getattr(mod, 'Scene', None)
            if SceneClass is None:
                print(f"No Scene class in {scene_module_name}")
                return
            self.current_scene = SceneClass()
            self.current_scene.setup()
            # optionally play music
            if self.current_scene.name==2: # pour éviter de charger la music à chaque fois
                if getattr(self.current_scene, 'background_music', None):
                    try:
                        arcade.play_sound(self.current_scene.background_music, volume=0.2)
                    except Exception:
                        pass
        except Exception as e:
            print('Failed to load scene module', e)

    def on_draw(self):
        self.clear()
        if self.current_scene:
            self.current_scene.on_draw()

    def on_update(self, delta_time):
        if self.current_scene:
            self.current_scene.on_update(delta_time)
            # If player dead and next scene defined, switch
            if getattr(self.current_scene, 'player_health', 1) <= 0:
                next_mod = getattr(self.current_scene, 'next_scene_module', None)
                if next_mod:
                    print(f"Switching to scene {next_mod}")
                    self.setup_scene(next_mod)

    def on_key_press(self, key, modifiers):
        if self.current_scene:
            self.current_scene.on_key_press(key, modifiers)

    def on_key_release(self, key, modifiers):
        if self.current_scene:
            self.current_scene.on_key_release(key, modifiers)

if __name__ == '__main__':
    window = MainWindow(SCREEN_WIDTH, SCREEN_HEIGHT, "Game with scenes")
    window.setup_scene('scene1')
    arcade.run()
