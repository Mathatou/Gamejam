import importlib
import os
import time
import arcade
from arcade.types import LRBT
from arcade import gl

from CutscenePlayer import CutscenePlayer

# --- Game constants ---
SCREEN_TITLE = "Hold'em!"
VIRTUAL_W, VIRTUAL_H = 640, 480
ASPECT = VIRTUAL_W / VIRTUAL_H
start_time = 0

# ---------------- Main view ----------------
class MainView(arcade.View):
    def __init__(self, window):
        super().__init__(window)
        self.background_color = arcade.color.BLACK

        self.game_cam = arcade.Camera2D(
            position=(16*2, 0),
            projection=LRBT(0, VIRTUAL_W, 0, VIRTUAL_H),
            viewport=self.window.rect,
        )

        arcade.SpriteList.DEFAULT_TEXTURE_FILTER = gl.NEAREST, gl.NEAREST

        self.current_scene = None
        self.scene_module = None

        # Cutscene state
        self.video_player: CutscenePlayer | None = None
        self.next_scene_after_video: str | None = None

        self._fit_viewport()

    def start_timer(self):
        global start_time
        start_time = time.perf_counter()
        print("Début du décompte : ", start_time)

    # -------------- camera / viewport --------------
    def _fit_viewport(self):
        self.game_cam.match_window(viewport=True, projection=False, aspect=ASPECT)

    # -------------- scene loading --------------
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
        except Exception as e:
            print('[MainView] Failed to load scene module', scene_module_name, e)

    # -------------- cutscene control --------------
    def play_video(self, file_path: str, next_scene: str | None):
        self.stop_video()  # safety

        vp = CutscenePlayer(file_path)
        if not vp.open():
            print("⚠️ Could not start OpenCV playback. Skipping to next scene.")
            if next_scene:
                self.setup_scene(next_scene)
            return

        self.video_player = vp
        self.next_scene_after_video = next_scene
        print(f"▶️ Playing cutscene via OpenCV: {file_path}")

    def stop_video(self):
        if self.video_player:
            try:
                self.video_player.close()
            except Exception:
                pass
        self.video_player = None

    # -------------- arcade lifecycle --------------
    def on_show_view(self):
        self._fit_viewport()

    def on_resize(self, width: int, height: int):
        self._fit_viewport()
        if self.current_scene and hasattr(self.current_scene, "on_resize"):
            self.current_scene.on_resize(width, height)

    def on_draw(self):
        self.clear()
        with self.game_cam.activate():
            if self.video_player and not self.video_player.finished:
                self.video_player.draw(0, 0, VIRTUAL_W, VIRTUAL_H)
            elif self.current_scene and hasattr(self.current_scene, "on_draw"):
                self.current_scene.on_draw()

    def on_update(self, delta_time: float):
        # If a cutscene is playing
        if self.video_player and not self.video_player.finished:
            self.video_player.update(delta_time)
            if self.video_player.finished:
                next_mod = self.next_scene_after_video
                self.stop_video()
                if next_mod:
                    print(f"🎬 Cutscene finished. Loading {next_mod}")
                    self.setup_scene(next_mod)
            return

        # Otherwise, normal scene update
        if self.current_scene and hasattr(self.current_scene, "on_update"):
            self.current_scene.on_update(delta_time)

            # When scene1 ends, play MP4 then go to scene2
            # Keep compatibility with your previous trigger:
            if getattr(self.current_scene, 'player_health', 1) <= 0:
                if getattr(self.current_scene, "name", None) == 1:
                    video_path = os.path.join(os.path.dirname(__file__), "assets", "videos", "scene1.mp4")
                    next_scene = getattr(self.current_scene, 'next_scene_module', 'scene2')
                    self.play_video(video_path, next_scene)
                    return

                # Other scenes: jump straight to their declared next scene
                next_mod = getattr(self.current_scene, 'next_scene_module', None)
                if next_mod:
                    print(f"Switching to scene {next_mod}")
                    self.setup_scene(next_mod)

    # -------------- inputs --------------
    def on_key_press(self, key, modifiers):
        # Allow skipping the cutscene
        if self.video_player and not self.video_player.finished:
            if key in (arcade.key.SPACE, arcade.key.ENTER, arcade.key.ESCAPE):
                print("⏭️ Cutscene skipped.")
                next_mod = self.next_scene_after_video
                self.stop_video()
                if next_mod:
                    self.setup_scene(next_mod)
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
