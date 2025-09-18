# ---------------- MP4 cutscene (OpenCV-only) ----------------
import pyglet


class CutscenePlayer:
    """
    Decodes frames with OpenCV and draws them via pyglet ImageData.
    """
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.cap = None          # cv2.VideoCapture
        self.fps = 30.0
        self._accum = 0.0
        self.finished = False
        self._pyg_image = None   # pyglet.image.ImageData
        self._w = 0
        self._h = 0

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
        return True

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
