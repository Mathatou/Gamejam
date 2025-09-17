import importlib
from arcade.types import LRBT, LBWH
from arcade import gl
import time
import arcade
import os

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
            position=(16 * 2, 16 * 0),
            projection=LRBT(0, VIRTUAL_W, 0, VIRTUAL_H),
            viewport=self.window.rect,
        )

        arcade.SpriteList.DEFAULT_TEXTURE_FILTER = gl.NEAREST, gl.NEAREST

        # Gestion de scène (objet "Scene" non-View avec .on_draw/.on_update/...)
        self.current_scene = None
        self.scene_module = None
        self.background_player = None

        # Système vidéo (séquence d’images)
        self.video_frames = []
        self.video_index = 0
        self.video_timer = 0
        self.video_fps = 30
        self.playing_video = False
        self.next_scene_after_video = None

        # Ajuste la viewport dès l'affichage
        self._fit_viewport()

    def start_Timer(self):
        global start_time
        start_time = time.perf_counter()
        print("Début du décompte : ", start_time)

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

    # ---------------- Vidéo (images séquentielles) ----------------
    def load_video_frames(self, folder_path: str):
        """Charge toutes les images d’un dossier comme des frames vidéo."""
        frames = []
        for fname in sorted(os.listdir(folder_path)):
            if fname.lower().endswith((".png", ".jpg", ".jpeg")):
                path = os.path.join(folder_path, fname)
                sprite = arcade.Sprite(path, center_x=VIRTUAL_W // 2, center_y=VIRTUAL_H // 2)
                frames.append(sprite)
        if frames:
            self.video_frames = frames
            self.video_index = 0
            self.video_timer = 0
            self.playing_video = True
            print(f"▶️ Vidéo chargée ({len(frames)} frames)")
        else:
            print(f"⚠️ Aucune image trouvée dans {folder_path}")

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
            if self.playing_video and self.video_frames:
                # Dessine la frame courante
                self.video_frames[self.video_index].draw()
            elif self.current_scene and hasattr(self.current_scene, "on_draw"):
                self.current_scene.on_draw()

    def on_update(self, delta_time: float):
        if self.playing_video and self.video_frames:
            # Avancer la vidéo à 30 FPS
            self.video_timer += delta_time
            if self.video_timer >= 1 / self.video_fps:
                self.video_timer = 0
                self.video_index += 1
                if self.video_index >= len(self.video_frames):
                    # Vidéo terminée → passer à la prochaine scène
                    self.playing_video = False
                    if self.next_scene_after_video:
                        self.setup_scene(self.next_scene_after_video)
            return

        # Sinon comportement normal
        if self.current_scene and hasattr(self.current_scene, "on_update"):
            self.current_scene.on_update(delta_time)
            if getattr(self.current_scene, 'player_health', 1) <= 0:
                # Déclenche la vidéo si name == 1
                if getattr(self.current_scene, "name", None) == 1:
                    folder = os.path.join(os.path.dirname(__file__), "assets", "videos")
                    self.load_video_frames(folder)
                    self.next_scene_after_video = getattr(self.current_scene, 'next_scene_module', None)
                    return

                # Sinon passe directement à la scène suivante
                next_mod = getattr(self.current_scene, 'next_scene_module', None)
                if next_mod:
                    print(f"Switching to scene {next_mod}")
                    self.setup_scene(next_mod)

    # ---------------- Entrées clavier / souris ----------------
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
