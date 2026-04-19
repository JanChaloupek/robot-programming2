import time
import board
import digitalio
import pwmio
from picoed import display, i2c

ARDUINO_ADDR = 0x08
PULSES_PER_REV = 960  # počet pulsů na jednu otáčku

# --- Pomocné funkce ---
def read_uint32(buf, offset):
    return buf[offset] | (buf[offset+1] << 8) | (buf[offset+2] << 16) | (buf[offset+3] << 24)

def read_encoder(cmd):
    while not i2c.try_lock():
        pass
    try:
        i2c.writeto(ARDUINO_ADDR, bytes([cmd]))
        buf = bytearray(13)
        i2c.readfrom_into(ARDUINO_ADDR, buf)
        forward = read_uint32(buf, 0)
        backward = read_uint32(buf, 4)
        direction = buf[8]
        lastPulse = read_uint32(buf, 9)
        return {"forward": forward, "backward": backward, "dir": direction, "lastPulse": lastPulse}
    finally:
        i2c.unlock()

def arduino_reset():
    while not i2c.try_lock():
        pass
    try:
        # Pošli příkaz 1 = reset
        i2c.writeto(ARDUINO_ADDR, bytes([0x01]))
        buf = bytearray(2)
        i2c.readfrom_into(ARDUINO_ADDR, buf)
        reply = buf.decode("utf-8")
        print("Arduino odpověď:", reply)
    finally:
        i2c.unlock()

# --- Motor M1 (levý) ---
ain1 = digitalio.DigitalInOut(board.P8); ain1.direction = digitalio.Direction.OUTPUT
pwma = pwmio.PWMOut(board.P1, frequency=1000)

def m1_forward(s):
    ain1.value = True   # dopředu
    pwma.duty_cycle = s

def m1_backward(s):
    ain1.value = False  # dozadu
    pwma.duty_cycle = s

def m1_stop():
    pwma.duty_cycle = 0

# --- Motor M2 (pravý) ---
ain2 = digitalio.DigitalInOut(board.P12); ain2.direction = digitalio.Direction.OUTPUT
pwmb = pwmio.PWMOut(board.P2, frequency=1000)

def m2_forward(s):
    ain2.value = True   # dopředu
    pwmb.duty_cycle = s

def m2_backward(s):
    ain2.value = False  # dozadu
    pwmb.duty_cycle = s

def m2_stop():
    pwmb.duty_cycle = 0

# --- Logika: 10 otáček dopředu a zpět ---   
def run_rotations(rotations=10, speed=30000, slow_speed=3000, slowdown_threshold=0.9):
    """
    rotations: počet otáček
    speed: plná rychlost (PWM duty_cycle)
    slow_speed: absolutní hodnota PWM pro zpomalený chod
    slowdown_threshold: kdy začít zpomalovat (např. 0.9 = po 90 % cesty)
    """
    target = rotations * PULSES_PER_REV
    slowdown_point = int(target * slowdown_threshold)

    print(f"Jedeme dopředu a zpět o {rotations} otáček (cílové pulsy: {target}, zpomalení na PWM={slow_speed})")
    display.show("Fwd")

    # --- Dopředu ---
    start_m1 = read_encoder(0x11)["forward"]
    start_m2 = read_encoder(0x21)["forward"]

    m1_forward(speed)
    m2_forward(speed)

    done_m1 = done_m2 = False
    slowed_m1 = slowed_m2 = False

    while not (done_m1 and done_m2):
        m1 = read_encoder(0x11)
        m2 = read_encoder(0x21)

        delta_m1 = m1["forward"] - start_m1
        delta_m2 = m2["forward"] - start_m2

#        print(f"M1 fwd={m1['forward']} Δ={delta_m1} | M2 fwd={m2['forward']} Δ={delta_m2}")

        if not slowed_m1 and delta_m1 >= slowdown_point:
            m1_forward(slow_speed)
            slowed_m1 = True
            print("Levý motor zpomaluje")
        if not done_m1 and delta_m1 >= target:
            m1_stop()
            done_m1 = True
            print(f"Levý motor zastaven na {m1['forward']} (Δ={delta_m1})")

        if not slowed_m2 and delta_m2 >= slowdown_point:
            m2_forward(slow_speed)
            slowed_m2 = True
            print("Pravý motor zpomaluje")
        if not done_m2 and delta_m2 >= target:
            m2_stop()
            done_m2 = True
            print(f"Pravý motor zastaven na {m2['forward']} (Δ={delta_m2})")

        time.sleep(0.05)

    print("Hotovo: dopředu")

    display.show("Pau")
    time.sleep(2)

    display.show("Bck")

    # --- Zpět ---
    start_m1 = read_encoder(0x11)["backward"]
    start_m2 = read_encoder(0x21)["backward"]

    m1_backward(speed)
    m2_backward(speed)

    done_m1 = done_m2 = False
    slowed_m1 = slowed_m2 = False

    while not (done_m1 and done_m2):
        m1 = read_encoder(0x11)
        m2 = read_encoder(0x21)

        delta_m1 = m1["backward"] - start_m1
        delta_m2 = m2["backward"] - start_m2

#        print(f"M1 back={m1['backward']} Δ={delta_m1} | M2 back={m2['backward']} Δ={delta_m2}")

        if not slowed_m1 and delta_m1 >= slowdown_point:
            m1_backward(slow_speed)
            slowed_m1 = True
            print("Levý motor zpomaluje")
        if not done_m1 and delta_m1 >= target:
            m1_stop()
            done_m1 = True
            print(f"Levý motor zastaven na {m1['backward']} (Δ={delta_m1})")

        if not slowed_m2 and delta_m2 >= slowdown_point:
            m2_backward(slow_speed)
            slowed_m2 = True
            print("Pravý motor zpomaluje")
        if not done_m2 and delta_m2 >= target:
            m2_stop()
            done_m2 = True
            print(f"Pravý motor zastaven na {m2['backward']} (Δ={delta_m2})")

        time.sleep(0.05)

    display.show("End")
    print("Hotovo: zpět")
    

# --- Spuštění ---
if __name__ == "__main__":
    arduino_reset()  # nejdřív reset → Arduino vrátí "OK"
    for i in range(9, 0, -1):
        display.show("{}  ".format(i))
        time.sleep(1)
    run_rotations(rotations=10, speed=20000, slow_speed=5000, slowdown_threshold=0.98)
