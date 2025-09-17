import importlib
from arcade.types import LRBT, LBWH
from arcade import gl
import time
from MenuView import *

# --- Constantes ---
SCREEN_TITLE = "Hold'em!"
VIRTUAL_W, VIRTUAL_H = 640, 480            # résolution « virtuelle » fixe 4:3
ASPECT = VIRTUAL_W / VIRTUAL_H             # 1.333...
start_time = 0

class MainView(arcade.View):
    def __init__(self, window):
        super().__init__(window)
        self.background_color = arcade.color.BLACK

        # Caméra du jeu : projection fixe 640x480
        self.game_cam = arcade.Camera2D(
            position=(16*2, 16*0),
            projection=LRBT(0, VIRTUAL_W, 0, VIRTUAL_H),
            viewport=self.window.rect,
        )

        arcade.SpriteList.DEFAULT_TEXTURE_FILTER = gl.NEAREST, gl.NEAREST

        # Gestion de scène (objet "Scene" non-View avec .on_draw/.on_update/...)
        self.current_scene = None
        self.scene_module = None
        self.background_player = None

        # Ajuste la viewport dès l'affichage
        self._fit_viewport()

    def start_Timer(self):
        global start_time
        start_time = time.perf_counter()
        print("Début du décompte : ",start_time)


    # ---------------- Camera / Viewport ----------------
    def _fit_viewport(self):
        self.game_cam.match_window(viewport=True, projection=False, aspect=ASPECT)

    # ---------------- Scènes ----------------
    def setup_scene(self, scene_module_name='scene1'):
        try:
            mod = importlib.import_module(scene_module_name)
            SceneClass = getattr(mod, 'Scene', None)
            if SceneClass is None:
                print(f"No Scene class in {scene_module_name}")
                return
            self.scene_module = mod
            self.current_scene = SceneClass()
            if hasattr(self.current_scene, "setup"):
                self.current_scene.setup()

            # (Option) musique de fond de la scène courante
            if getattr(self.current_scene, 'background_music', None):
                try:
                    arcade.play_sound(self.current_scene.background_music, volume=0.2)
                except Exception:
                    pass
        except Exception as e:
            print('[MainView] Failed to load scene module', scene_module_name, e)

    # ---------------- Cycle de vie & événements ----------------
    def on_show_view(self):
        self._fit_viewport()

    def on_resize(self, width: int, height: int):
        self._fit_viewport()
        if self.current_scene and hasattr(self.current_scene, "on_resize"):
            self.current_scene.on_resize(width, height)

    def on_draw(self):
        self.clear()

        with self.game_cam.activate():
            if self.current_scene and hasattr(self.current_scene, "on_draw"):
                self.current_scene.on_draw()

    def on_update(self, delta_time: float):
        if self.current_scene and hasattr(self.current_scene, "on_update"):
            self.current_scene.on_update(delta_time)
            # If player dead and next scene defined, switch
            if getattr(self.current_scene, 'player_health', 1) <= 0:
                next_mod = getattr(self.current_scene, 'next_scene_module', None)
                if next_mod:
                    print(f"Switching to scene {next_mod}")
                    self.setup_scene(next_mod)

    def on_key_press(self, key, modifiers):
        if key == arcade.key.ESCAPE:
            self.window.close()
            return
        if self.current_scene and hasattr(self.current_scene, "on_key_press"):
            self.current_scene.on_key_press(key, modifiers)

    def on_key_release(self, key, modifiers):
        if self.current_scene and hasattr(self.current_scene, "on_key_release"):
            self.current_scene.on_key_release(key, modifiers)

    def on_mouse_motion(self, x, y, dx, dy):
        if self.current_scene and hasattr(self.current_scene, "on_mouse_motion"):
            self.current_scene.on_mouse_motion(x, y, dx, dy)

    def on_mouse_press(self, x, y, button, modifiers):
        if self.current_scene and hasattr(self.current_scene, "on_mouse_press"):
            self.current_scene.on_mouse_press(x, y, button, modifiers)

    def on_mouse_release(self, x, y, button, modifiers):
        if self.current_scene and hasattr(self.current_scene, "on_mouse_release"):
            self.current_scene.on_mouse_release(x, y, button, modifiers)

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        if self.current_scene and hasattr(self.current_scene, "on_mouse_drag"):
            self.current_scene.on_mouse_drag(x, y, dx, dy, buttons, modifiers)

    def on_mouse_scroll(self, x, y, scroll_x, scroll_y):
        if self.current_scene and hasattr(self.current_scene, "on_mouse_scroll"):
            self.current_scene.on_mouse_scroll(x, y, scroll_x, scroll_y)


if __name__ == '__main__':
    window = arcade.Window(width=960, height=720, title=SCREEN_TITLE, resizable=True)

    from MenuView import MenuView
    window.show_view(MenuView())

    arcade.run()
