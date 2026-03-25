from luma.core.interface.serial import spi
from luma.oled.device import sh1106

serial = spi(
    port=0,
    device=1,       # CE1 (GPIO7, pin 26)
    gpio_DC=25,     # pin 22
    gpio_RST=27,    # pin 13
    bus_speed_hz=1000000
)

device = sh1106(serial, rotate=0)
