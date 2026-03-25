from luma.core.interface.serial import spi
from luma.oled.device import sh1106
from PIL import Image, ImageDraw
import time
import math

# ==== KONFIGURACJA SPRZĘTOWA (TWOJA) ====
serial = spi(
    port=0,
    device=1,       # CE1 (GPIO7 / pin 26)
    gpio_DC=25,     # pin 22
    gpio_RST=27,    # pin 13
    bus_speed_hz=1000000
)
device = sh1106(serial)

WIDTH = device.width
HEIGHT = device.height

# ==== PARAMETRY OCZU ====
EYE_RADIUS = 10
PUPIL_RADIUS = 4

LEFT_EYE_X = 42
RIGHT_EYE_X = 86
EYE_Y = 32


def clear():
    img = Image.new("1", (WIDTH, HEIGHT))
    device.display(img)


def draw_eyes(pupil_offset_x=0, blink=1.0, smile=False):
    img = Image.new("1", (WIDTH, HEIGHT))
    d = ImageDraw.Draw(img)

    eye_height = int(EYE_RADIUS * blink)

    for x in (LEFT_EYE_X, RIGHT_EYE_X):
        if smile:
            d.arc(
                (x - EYE_RADIUS, EYE_Y - EYE_RADIUS,
                 x + EYE_RADIUS, EYE_Y + EYE_RADIUS),
                start=200, end=340, fill=1
            )
        else:
            d.ellipse(
                (x - EYE_RADIUS, EYE_Y - eye_height,
                 x + EYE_RADIUS, EYE_Y + eye_height),
                outline=1, fill=1
            )

            d.ellipse(
                (x - PUPIL_RADIUS + pupil_offset_x,
                 EYE_Y - PUPIL_RADIUS,
                 x + PUPIL_RADIUS + pupil_offset_x,
                 EYE_Y + PUPIL_RADIUS),
                outline=0, fill=0
            )

    device.display(img)


# ===== STANY ROBOTA =====

def eyes_listening(duration=2):
    end = time.time() + duration
    while time.time() < end:
        draw_eyes()
        time.sleep(0.1)


def eyes_thinking(duration=3):
    end = time.time() + duration
    t = 0
    while time.time() < end:
        offset = int(5 * math.sin(t))
        draw_eyes(pupil_offset_x=offset)
        t += 0.3
        time.sleep(0.1)


def eyes_speaking(duration=3):
    end = time.time() + duration
    blink = True
    while time.time() < end:
        if blink:
            draw_eyes(smile=True)
        else:
            draw_eyes(blink=0.2)
        blink = not blink
        time.sleep(0.2)


def eyes_idle():
    while True:
        draw_eyes()
        time.sleep(3)
        draw_eyes(blink=0.1)
        time.sleep(0.15)
        draw_eyes()


# ==== TEST ====
if __name__ == "__main__":
    try:
        eyes_listening()
        eyes_thinking()
        eyes_speaking()
        eyes_idle()
    except KeyboardInterrupt:
        clear()
