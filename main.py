#--- main.py ---
import importlib
from MenuView import *

# --- Constantes ---
SCREEN_WIDTH = 640
SCREEN_HEIGHT = 480
SCREEN_TITLE = "Hold'em!"

class MainView(arcade.View):
    def __init__(self, window):
        super().__init__(window)
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
    game = arcade.Window(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
    main_view = MenuView()
    game.show_view(main_view)
    arcade.run()
