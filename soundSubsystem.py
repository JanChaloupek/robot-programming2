from HardwarePlatform import PinPWM, pin16
from timer import Period

class HonkData:

    def __init__(self, tones, durations, pauses):
        """ Inicializace datové třídy pro sekvenci troubení """
        if not tones or not durations or not pauses:
            raise ValueError("Sekvence troubení musí obsahovat alespoň jeden tón, délku a pauzu!")
        
        self.tones = tones
        self.durations = durations
        self.pauses = pauses

honk_data = HonkData(
    tones=[1000, 1200, 900, 1000, 1100],
    durations=[150, 200, 100, 250, 180],
    pauses=[50, 80, 60, 100, 90]
)
tutu = HonkData(
    tones=[1000, 1000],
    durations=[500, 700],
    pauses=[50, 1]
)
warningShort = HonkData(
    tones=[1000, 1200],
    durations=[150, 200],
    pauses=[100, 100]
)
warningLong = HonkData(
    tones=[800, 900, 800],
    durations=[400, 500, 600],
    pauses=[150, 150, 200]
)
hello = HonkData(
    tones=[1000, 1300, 1500, 1300, 1000],
    durations=[200, 150, 180, 150, 200],
    pauses=[100, 80, 90, 80, 100]
)
panic = HonkData(
    tones=[1000, 1100, 1200, 1300, 1400],
    durations=[300, 300, 300, 300, 300],
    pauses=[50, 50, 50, 50, 50]
)
# brzdeni = HonkData(
#     tones=[2000, 1800, 1600, 1400, 1200, 1000, 800, 600],  # Frekvence postupně klesají
#     durations=[150, 180, 200, 220, 250, 280, 300, 350],  # Délky tónů se prodlužují
#     pauses=[50, 70, 90, 120, 150, 180, 200, 250]  # Pauzy mezi tóny se prodlužují
# )
brzdeni = HonkData(
    tones=[5000, 4000, 3000, 2500, 2000, 1500, 1000],  # Rychlé vysokofrekvenční vibrace postupně klesají
    durations=[100, 120, 140, 160, 180, 200, 250],  # Délky vibrací se prodlužují
    pauses=[20, 40, 60, 80, 100, 120, 150]  # Pauzy mezi pulzy se zvyšují, napodobující zpomalování
)


class HornController:
    def __init__(self):
        self.pin_pwm = pin16
        self.data = None
        self.index = 0
        self.period = None
        self.is_honking = True
        self.playing = False

    def play_honk(self, honk_data: HonkData):
        """ Spustí novou sekvenci tónů na základě `HonkData` """
        self.data = honk_data
        self.index = 0
        self.is_honking = True
        self.playing = True
        self.period = Period(self.data.durations[self.index])  # Inicializace časovače
        self.set_pwm_frequency()

    def set_pwm_frequency(self):
        """ Nastaví frekvenci PWM na aktuální tón """
        freq = self.data.tones[self.index]
        self.pin_pwm.set_analog_period(1000 / freq)  # Převod frekvence na periodu
        self.pin_pwm.write_analog(30000 if self.is_honking else 0)  # Aktivace nebo pauza

    def update(self):
        """ Aktualizace troubení podle časovače """
        if self.playing and self.period.isTime():
            if self.is_honking:
                self.pin_pwm.write_analog(0)  # Pauza
                self.is_honking = False
                self.period.startTimer(None, self.data.pauses[self.index])
            else:
                self.index += 1
                if self.index >= len(self.data.tones):
                    self.playing = False
                    self.pin_pwm.write_analog(0)  # Vypnutí PWM
                    return
                self.is_honking = True
                self.set_pwm_frequency()  # Nastavení nové frekvence
                self.period.startTimer(None, self.data.durations[self.index])

