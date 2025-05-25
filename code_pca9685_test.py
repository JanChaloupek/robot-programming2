from HardwarePlatform import i2c, button_a, sleep
from motionSubsystem import PCA9633, PCA9685

if __name__ == "__main__": 

    pca9633 = PCA9633(i2c, 0x62)
    pca9633.writeRegister(PCA9633.RegMODE1, 0x00)   # vypni sleep a všechny SW adresy
    
    pca9685 = PCA9685(i2c, 0x61)
    pca9685.writeRegister(PCA9685.RegMODE1, PCA9685.RegMODE1_VALUE)   # vypni sleep a všechny SW adresy (povol auto increment)

    while not button_a.was_pressed():
        for i in range(4096):
            pca9685.writePwmToHbridge(0, i)
            pca9685.writePwmToHbridge(2, i)
            sleep(100)
        for i in range(4096):
            pca9685.writePwmToHbridge(0, -i)
            pca9685.writePwmToHbridge(2, -i)
            sleep(100)
