from luma.core.interface.serial import spi
from luma.oled.device import sh1106
import time
from eyes.engine import EyesEngine

# OLED init
serial = spi(
    port=0,
    device=1,
    gpio_DC=25,
    gpio_RST=27,
    bus_speed_hz=8000000
)
oled = sh1106(serial)

eyes = EyesEngine(oled, fps=60)

try:
    while True:
        print("LISTENING")
        eyes.listening()
        time.sleep(3)

        print("THINKING")
        eyes.thinking()
        time.sleep(3)

        print("SPEAKING")
        eyes.speaking()
        time.sleep(3)

except KeyboardInterrupt:
    eyes.stop()
