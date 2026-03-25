import time
import random
import threading
from luma.core.interface.serial import spi
from luma.oled.device import sh1106
from PIL import Image, ImageDraw


class EyesEngine(threading.Thread):
    """
    Eyes engine based on the user's 'best version' test script.
    Runs at ~60 Hz in a background thread and exposes set_mode() API.
    """

    def __init__(
        self,
        port=0,
        device=1,
        gpio_DC=25,
        gpio_RST=27,
        bus_speed_hz=8_000_000,
        fps=60,
    ):
        super().__init__(daemon=True)

        # ================= OLED =================
        self.serial = spi(
            port=port,
            device=device,
            gpio_DC=gpio_DC,
            gpio_RST=gpio_RST,
            bus_speed_hz=bus_speed_hz,
        )
        self.oled = sh1106(self.serial)
        self.W, self.H = self.oled.width, self.oled.height

        # ================= PARAMETRY OCZU (jak u Ciebie) =================
        self.REF_W = int(40 * 0.8)
        self.REF_H = int(40 * 0.8)
        self.RADIUS = 8
        self.SPACE = 10

        self.cx = self.W // 2
        self.cy = self.H // 2

        self.left_base_x = self.cx - self.REF_W // 2 - self.SPACE // 2
        self.right_base_x = self.cx + self.REF_W // 2 + self.SPACE // 2

        # ================= STAN (jak u Ciebie) =================
        self.eye_w = float(self.REF_W)
        self.eye_h = float(self.REF_H)

        self.offset_x = 0.0
        self.offset_y = 0.0

        self.target_w = float(self.REF_W)
        self.target_h = float(self.REF_H)
        self.target_x = 0.0
        self.target_y = 0.0

        # deformacja: None | "inward" | "outward"
        self.deform = None

        # ================= STEROWANIE =================
        self.mode = "WAKEUP"
        self.running = True
        self.fps = fps

        self._last_event = time.time()
        self._next_event_in = random.uniform(1.2, 2.8)

        # wakeup stan początkowy
        self.eye_h = 2.0

        self.start()

    # ================= PUBLIC API =================
    def set_mode(self, mode: str) -> None:
        # dopuszczalne: WAKEUP, IDLE, LISTENING, THINKING, SPEAKING, SLEEP
        self.mode = mode
        # przy zmianie trybu przyspieszamy "event" żeby reakcja była natychmiastowa
        self._last_event = 0
        self._next_event_in = 0.01

    def stop(self) -> None:
        self.running = False

    # ================= RYSOWANIE (jak u Ciebie) =================
    @staticmethod
    def _cut_top_left(d: ImageDraw.ImageDraw, x0: int, y0: int, cut: int) -> None:
        d.polygon([(x0, y0), (x0 + cut, y0), (x0, y0 + cut)], fill=0)

    @staticmethod
    def _cut_top_right(d: ImageDraw.ImageDraw, x1: int, y0: int, cut: int) -> None:
        d.polygon([(x1, y0), (x1 - cut, y0), (x1, y0 + cut)], fill=0)

    def _draw_eye(self, d: ImageDraw.ImageDraw, x: int, y: int, is_left_eye: bool, deform_type=None) -> None:
        eye_w = int(self.eye_w)
        eye_h = int(self.eye_h)

        x0 = x - eye_w // 2
        y0 = y - eye_h // 2
        x1 = x + eye_w // 2
        y1 = y + eye_h // 2

        d.rounded_rectangle(
            (x0, y0, x1, y1),
            radius=min(self.RADIUS, int(eye_h) // 2),
            fill=1,
        )

        cut = max(6, eye_w // 4)

        if deform_type == "inward":
            # WEWNĘTRZNE narożniki: bliżej środka twarzy
            # lewe oko -> prawy górny, prawe oko -> lewy górny
            if is_left_eye:
                self._cut_top_right(d, x1, y0, cut)
            else:
                self._cut_top_left(d, x0, y0, cut)

        elif deform_type == "outward":
            # ZEWNĘTRZNE narożniki: na zewnątrz twarzy
            # lewe oko -> lewy górny, prawe oko -> prawy górny
            if is_left_eye:
                self._cut_top_left(d, x0, y0, cut)
            else:
                self._cut_top_right(d, x1, y0, cut)

    def _draw(self) -> None:
        img = Image.new("1", (self.W, self.H))
        d = ImageDraw.Draw(img)

        # lewe
        self._draw_eye(
            d,
            self.left_base_x + int(self.offset_x),
            self.cy + int(self.offset_y),
            is_left_eye=True,
            deform_type=self.deform,
        )

        # prawe
        self._draw_eye(
            d,
            self.right_base_x + int(self.offset_x),
            self.cy + int(self.offset_y),
            is_left_eye=False,
            deform_type=self.deform,
        )

        self.oled.display(img)

    # ================= PŁYNNOŚĆ (jak u Ciebie) =================
    def _smooth(self) -> None:
        self.eye_w += (self.target_w - self.eye_w) * 0.18
        self.eye_h += (self.target_h - self.eye_h) * 0.18
        self.offset_x += (self.target_x - self.offset_x) * 0.25
        self.offset_y += (self.target_y - self.offset_y) * 0.25

    # ================= EMOCJE / AKCJE (jak u Ciebie + mapowanie trybów) =================
    def _look_fast(self) -> None:
        self.target_x = random.choice([-14, -8, 0, 8, 14])
        self.target_y = random.choice([-6, 0, 5])

    def _bored(self) -> None:
        self.target_h = float(int(self.REF_H * 0.6))
        self.deform = None

    def _neutral(self) -> None:
        self.target_w = float(self.REF_W)
        self.target_h = float(self.REF_H)
        self.deform = None

    def _frown_inward(self) -> None:
        self.deform = "inward"
        self.target_h = float(int(self.REF_H * 0.8))

    def _frown_outward(self) -> None:
        self.deform = "outward"
        self.target_h = float(int(self.REF_H * 0.75))

    def _surprise(self) -> None:
        self.target_w = float(int(self.REF_W * 1.15))
        self.target_h = float(int(self.REF_H * 1.3))
        self.deform = None

    def _blink(self) -> None:
        # identyczny feeling jak u Ciebie (tylko na self.*)
        start_h = int(self.eye_h)
        for h in range(start_h, 6, -8):
            self.eye_h = float(h)
            self._draw()
            time.sleep(0.008)
        for h in range(6, self.REF_H + 1, 8):
            self.eye_h = float(h)
            self._draw()
            time.sleep(0.008)

    def _wakeup(self) -> None:
        # miękki start: od "prawie zamkniętych" do normalnych
        for h in range(2, self.REF_H + 1, 2):
            self.eye_h = float(h)
            self._neutral()
            self._draw()
            time.sleep(0.012)
        self._neutral()

    def _sleep(self) -> None:
        # oczy prawie zamknięte
        self.deform = None
        self.target_w = float(self.REF_W)
        self.target_h = float(4)

    # ================= MAIN LOOP (60 Hz) =================
    def run(self) -> None:
        dt = 1.0 / float(self.fps)

        # WAKEUP tylko raz po starcie
        if self.mode == "WAKEUP":
            self._wakeup()
            self.mode = "IDLE"
            self._last_event = time.time()
            self._next_event_in = random.uniform(1.2, 2.8)

        while self.running:
            now = time.time()

            # ---- Sterowanie trybami ----
            if self.mode == "SLEEP":
                self._sleep()

            elif self.mode == "LISTENING":
                # częściej rozglądanie + czasem blink
                if now - self._last_event > random.uniform(0.8, 1.6):
                    if random.random() < 0.75:
                        self._look_fast()
                        self._neutral()
                    else:
                        self._blink()
                    self._last_event = now

            elif self.mode == "THINKING":
                # bardziej „GLaDOS”: częściej inward + spojrzenia w bok/górę
                if now - self._last_event > random.uniform(0.6, 1.3):
                    if random.random() < 0.65:
                        self._frown_inward()
                        self.target_x = random.choice([-12, 12])
                        self.target_y = random.choice([-8, -4, 0])
                    else:
                        self._bored()
                        self.target_x = random.choice([-6, 0, 6])
                        self.target_y = 0
                    self._last_event = now

            elif self.mode == "SPEAKING":
                # spokojny, nie-chaotyczny mikroruch podczas mówienia
                self.deform = None
                self.target_h = float(int(self.REF_H * 0.85))
                if now - self._last_event > random.uniform(0.20, 0.40):
                    self.target_x = random.choice([-3, 0, 3])
                    self.target_y = random.choice([-1, 0, 1])
                    self._last_event = now

            else:  # IDLE
                # zachowanie 1:1 z testu: losowe eventy
                if now - self._last_event > self._next_event_in:
                    r = random.random()
                    if r < 0.25:
                        self._look_fast()
                    elif r < 0.40:
                        self._blink()
                    elif r < 0.55:
                        self._bored()
                    elif r < 0.70:
                        self._frown_inward()
                    elif r < 0.85:
                        self._frown_outward()
                    else:
                        self._surprise()

                    self._last_event = now
                    self._next_event_in = random.uniform(1.2, 2.8)

            self._smooth()
            self._draw()
            time.sleep(dt)
