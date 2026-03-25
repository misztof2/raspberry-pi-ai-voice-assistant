import time
import random
from luma.core.interface.serial import spi
from luma.oled.device import sh1106
from PIL import Image, ImageDraw

# ================= OLED =================
serial = spi(
    port=0,
    device=1,
    gpio_DC=25,
    gpio_RST=27,
    bus_speed_hz=8000000
)
oled = sh1106(serial)
W, H = oled.width, oled.height

# ================= PARAMETRY OCZU =================
REF_W = int(40 * 0.8)
REF_H = int(40 * 0.8)
RADIUS = 8
SPACE = 10

cx = W // 2
cy = H // 2

left_base_x = cx - REF_W // 2 - SPACE // 2
right_base_x = cx + REF_W // 2 + SPACE // 2

# ================= STAN =================
eye_w = REF_W
eye_h = REF_H

offset_x = 0
offset_y = 0

target_w = REF_W
target_h = REF_H
target_x = 0
target_y = 0

# deformacja: None | "inward" | "outward"
deform = None

# ================= RYSOWANIE =================
def cut_top_left(d, x0, y0, cut):
    # wycina trójkąt w lewym górnym rogu
    d.polygon([(x0, y0), (x0 + cut, y0), (x0, y0 + cut)], fill=0)

def cut_top_right(d, x1, y0, cut):
    # wycina trójkąt w prawym górnym rogu
    d.polygon([(x1, y0), (x1 - cut, y0), (x1, y0 + cut)], fill=0)

def draw_eye(d, x, y, is_left_eye: bool, deform_type=None):
    x0 = x - eye_w // 2
    y0 = y - eye_h // 2
    x1 = x + eye_w // 2
    y1 = y + eye_h // 2

    d.rounded_rectangle((x0, y0, x1, y1), radius=min(RADIUS, int(eye_h)//2), fill=1)

    cut = max(6, eye_w // 4)  # bezpiecznie, żeby było widać

    if deform_type == "inward":
        # WEWNĘTRZNE narożniki: bliżej środka twarzy
        # lewe oko -> prawy górny, prawe oko -> lewy górny
        if is_left_eye:
            cut_top_right(d, x1, y0, cut)
        else:
            cut_top_left(d, x0, y0, cut)

    elif deform_type == "outward":
        # ZEWNĘTRZNE narożniki: na zewnątrz twarzy
        # lewe oko -> lewy górny, prawe oko -> prawy górny
        if is_left_eye:
            cut_top_left(d, x0, y0, cut)
        else:
            cut_top_right(d, x1, y0, cut)

def draw():
    img = Image.new("1", (W, H))
    d = ImageDraw.Draw(img)

    # lewe
    draw_eye(
        d,
        left_base_x + int(offset_x),
        cy + int(offset_y),
        is_left_eye=True,
        deform_type=deform
    )

    # prawe
    draw_eye(
        d,
        right_base_x + int(offset_x),
        cy + int(offset_y),
        is_left_eye=False,
        deform_type=deform
    )

    oled.display(img)

# ================= PŁYNNOŚĆ =================
def smooth():
    global eye_w, eye_h, offset_x, offset_y
    eye_w += (target_w - eye_w) * 0.18
    eye_h += (target_h - eye_h) * 0.18
    offset_x += (target_x - offset_x) * 0.25
    offset_y += (target_y - offset_y) * 0.25

# ================= EMOCJE =================
def look_fast():
    global target_x, target_y
    target_x = random.choice([-14, -8, 0, 8, 14])
    target_y = random.choice([-6, 0, 5])

def bored():
    global target_h, deform
    target_h = int(REF_H * 0.6)
    deform = None

def neutral():
    global target_w, target_h, deform
    target_w = REF_W
    target_h = REF_H
    deform = None

# 😠 GNIEW / SKUPIENIE — DO ŚRODKA
def frown_inward():
    global deform, target_h
    deform = "inward"
    target_h = int(REF_H * 0.8)

# 😢 SMUTEK — NA ZEWNĄTRZ
def frown_outward():
    global deform, target_h
    deform = "outward"
    target_h = int(REF_H * 0.75)

# 😲 ZDZIWIENIE
def surprise():
    global target_w, target_h, deform
    target_w = int(REF_W * 1.15)
    target_h = int(REF_H * 1.3)
    deform = None

# ================= BLINK =================
def blink():
    global eye_h
    for h in range(int(eye_h), 6, -8):
        eye_h = h
        draw()
        time.sleep(0.008)
    for h in range(6, REF_H + 1, 8):
        eye_h = h
        draw()
        time.sleep(0.008)

# ================= MAIN LOOP =================
print("OLED EYES TEST — CTRL+C to exit")

last_event = time.time()

try:
    while True:
        now = time.time()

        if now - last_event > random.uniform(1.2, 2.8):
            r = random.random()

            if r < 0.25:
                look_fast()
            elif r < 0.4:
                blink()
            elif r < 0.55:
                bored()
            elif r < 0.7:
                frown_inward()
            elif r < 0.85:
                frown_outward()
            else:
                surprise()

            last_event = now

        smooth()
        draw()
        time.sleep(1/60)

except KeyboardInterrupt:
    print("Exit")
