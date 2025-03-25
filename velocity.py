
class Velocity:
    # třída pro uložení požadované rychlosti robota
    def __init__(self) -> None:
        self.forward = 0.0
        self.angular = 0.0

    def __str__(self):
        return "forward="+str(self.forward) + " angular="+str(self.angular)