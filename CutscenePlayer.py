# ---------------- MP4 cutscene (OpenCV + pyglet audio) ----------------
import pyglet
import threading


class CutscenePlayer:
    """
    Decode les frames avec OpenCV et les dessine via pyglet ImageData.
    Joue aussi l'audio en parallèle avec pyglet.media.
    """
    def __init__(self, file_path: str, audio_path: str):
        self.file_path = file_path
        self.audio_path = audio_path
        self.cap = None          # cv2.VideoCapture
        self.fps = 30.0
        self._accum = 0.0
        self.finished = False
        self._pyg_image = None   # pyglet.image.ImageData
        self._w = 0
        self._h = 0
        self._audio_player = None

    def open(self) -> bool:
        try:
            import cv2
        except Exception as e:
            print(f"⚠️ OpenCV not installed: {e}")
            self.finished = True
            return False

        cap = cv2.VideoCapture(self.file_path)
        if not cap.isOpened():
            print("⚠️ cv2.VideoCapture could not open:", self.file_path)
            self.finished = True
            return False

        fps = cap.get(5)  # CAP_PROP_FPS
        try:
            self.fps = float(fps) if fps and fps > 1e-6 else 30.0
        except Exception:
            self.fps = 30.0
        self.cap = cap

        # charger l'audio si fourni
        if self.audio_path:
            try:
                music = pyglet.media.load(self.audio_path, streaming=False)
                self._audio_player = pyglet.media.Player()
                self._audio_player.queue(music)
            except Exception as e:
                print(f"⚠️ Impossible de charger l'audio: {e}")

        return True

    def play_audio(self):
        if self._audio_player:
            self._audio_player.play()

    def update(self, dt: float):
        if self.finished or not self.cap:
            return

        import cv2

        # accumulate time and read as many frames as needed to keep up
        self._accum += dt
        frames_to_read = int(self._accum * self.fps)
        if frames_to_read < 1:
            return
        self._accum -= frames_to_read / self.fps

        ok, frame = False, None
        for _ in range(frames_to_read):
            ok, frame = self.cap.read()
            if not ok:
                break

        if not ok or frame is None:
            self.finished = True
            if self._audio_player:
                self._audio_player.pause()
            return

        # BGR -> RGB, flip vertically for GL-style coordinates
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, _ = frame.shape
        self._w, self._h = w, h
        pitch = -w * 3  # negative pitch flips vertically
        self._pyg_image = pyglet.image.ImageData(w, h, "RGB", frame.tobytes(), pitch=pitch)

    def draw(self, x: float, y: float, w: float, h: float):
        if self._pyg_image:
            self._pyg_image.blit(x, y, width=w, height=h)

    def close(self):
        if self.cap:
            try:
                self.cap.release()
            except Exception:
                pass
        self.cap = None
        self._pyg_image = None
        self.finished = True
        if self._audio_player:
            self._audio_player.delete()
