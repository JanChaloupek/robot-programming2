import board
import digitalio
import storage
from picoed import led, button_a, button_b
from HardwarePlatform import sleep

if not button_a.is_pressed():
    for i in range(10):
        led.toggle()
        sleep(1000)
    storage.remount("/", readonly=True)
if not button_a.is_pressed():
    for i in range(10):
        led.toggle()
        sleep(1000)
    storage.remount("/", readonly=True)
if not button_b.is_pressed():
    storage.remount("/", readonly=False)
