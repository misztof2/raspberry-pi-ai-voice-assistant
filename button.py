# button.py
from gpiozero import Button
from signal import pause

class WakeButton:
    def __init__(self, pin=17, callback=None):
        self.button = Button(pin, pull_up=True, bounce_time=0.1)
        if callback:
            self.button.when_pressed = callback

    def run_forever(self):
        pause()
