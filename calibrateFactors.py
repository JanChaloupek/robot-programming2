
class CalibrateFactors:
    # třída pro uložení kalibračních hodnot pro motor
    def __init__(self, minimumAngularSpeed:float, minPwm_WhenStopped:int, minPwm_InMotion:int, a:float, b:float) -> None:
        self.minimumAngularSpeed = minimumAngularSpeed
        self.__minPwm_WhenStopped = minPwm_WhenStopped
        self.__minPwm_InMotion = minPwm_InMotion
        self.__a = a
        self.__b = b
        # přičti zatěžový koeficient (pokud bude potřeba)
        self.__b += 40

    def calculatePwm(self, angularSpeed:float) -> int:
        # vypočti pwm pro danou uhlovou rychlost kola
        if angularSpeed == 0:
            return 0
        pwm = int(self.__a * abs(angularSpeed) + self.__b)
        if angularSpeed < 0:
            pwm *= -1
        return pwm

    def getMinimumPwm(self, isStopped:bool) -> int:
        if isStopped:
            return self.__minPwm_WhenStopped
        else:
            return self.__minPwm_InMotion

    def __str__(self) -> str:
        return "a="+str(self.__a)+" b="+str(self.__b)+" minSpeed="+str(self.minimumAngularSpeed)+" minPwmStopped="+str(self.__minPwm_WhenStopped)+" minPwmMotin="+str(self.__minPwm_InMotion)
