"""
Copyright 2020 LeMaRiva|Tech (Mauro Riva) info@lemariva.com

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

* Modified by Gian Luigi Perrella for M5Stack UI port.
added raw reading values of H2 and Ethanol
to do sending data via MQTT towards Openhab
"""

from m5stack import *
from m5ui import *
from uiflow import *
import gc
from machine import Pin, I2C
import ujson
import utime
import time

from sgp30 import SGP30
# from config import *
I2C_SCL_GPIO = const(22)
I2C_SDA_GPIO = const(21)
I2C_FREQ = const(100000)



epoch_offset = 946684800

## sgp30 setup
# i2c = SoftI2C(scl=Pin(22), sda=Pin(21), freq=100000)
i2c = machine.I2C(
    scl=machine.Pin(I2C_SCL_GPIO, machine.Pin.OUT),
    sda=machine.Pin(I2C_SDA_GPIO, machine.Pin.OUT),
    freq=I2C_FREQ
)
sgp30 = SGP30(i2c)
sgp30.initialise_indoor_air_quality()


def run():

#    if true:

    # Retrieve previously stored baselines, if any (helps the compensation algorithm).
    has_baseline = False
    try:
        f_co2 = open('co2eq_baseline.txt', 'r')
        f_tvoc = open('tvoc_baseline.txt', 'r')

        co2_baseline = int(f_co2.read())
        tvoc_baseline = int(f_tvoc.read())
        #Use them to calibrate the sensor
        sgp30.set_indoor_air_quality_baseline(co2_baseline, tvoc_baseline)

        f_co2.close()
        f_tvoc.close()

        has_baseline = True
    except:
        print('Impossible to read SGP30 baselines!')

    #Store the time at which last baseline has been saved
    baseline_time = utime.time()


    # acquiring and sending data
    while True:
        # acquiring data
        eco2, tvoc = sgp30.indoor_air_quality
        timestamp = utime.time() + epoch_offset
        level = "Normal"
        level_co2 = "Normal"
        if tvoc > 500:
            level = "Danger"
            print('TVOC Danger', + tvoc)
            
        elif tvoc > 250:
            level = "Warning"
            print('TVOC WARNING', + tvoc)
        else:
            print('TVOC:', + tvoc)
        print ('eCO2:' , + eco2)
        if eco2 > 1000:
            level_co2 = "Danger"
        label3.setText('CO2: ' + str(eco2) + " " + level_co2 + '\n' +
            'TVOC: ' + str(tvoc) + " " + level)
        time.sleep(1)
        h2, ethanol = sgp30.raw_air_quality
        timestamp = utime.time() + epoch_offset
        print('H2 measure', + h2)
        print('Ethanol measure', + ethanol)
#        label4.setText('H2: ' + str(h2) + '\n' +
 #           'Ethanol: ' + str(ethanol))
        time.sleep(1)
        
        gc.collect()

        # Baselines should be saved after 12 hour the first 
        # timen then every hour according to the doc.
        if (has_baseline and (utime.time() - baseline_time >= 3600)) \
            or ((not has_baseline) and (utime.time() - baseline_time >= 43200)):

            print('Saving baseline!')
            baseline_time = utime.time()

            try:
                f_co2 = open('co2eq_baseline.txt', 'w')
                f_tvoc = open('tvoc_baseline.txt', 'w')

                bl_co2, bl_tvoc = sgp30.indoor_air_quality_baseline
                f_co2.write(str(bl_co2))
                f_tvoc.write(str(bl_tvoc))

                f_co2.close()
                f_tvoc.close()

                has_baseline = True
            except:
                print('Impossible to write SGP30 baselines!')

        gc.collect()

setScreenColor(0xe9efd9)

image1 = M5Img(60, 100, "res/scolari2.jpg", True)
#label0 = M5TextBox(120, 40, "Status:", lcd.FONT_DejaVu24, 0xFF0000, rotate=0)
label1 = M5TextBox(90, 60, "", lcd.FONT_DejaVu24, 0xFF0000, rotate=0)
label2 = M5TextBox(25, 10, "M5 TVOC MONITOR", lcd.FONT_DejaVu24, 0xFF0000, rotate=0)
label3 = M5TextBox(0, 40, "", lcd.FONT_DejaVu18, 0xFF0000, rotate=0)
label4 = M5TextBox(0, 140, "", lcd.FONT_DejaVu18, 0xFF0000, rotate=0)
label5 = M5TextBox(90, 120, "", lcd.FONT_DejaVu24, 0xFF0000, rotate=0)
label6 = M5TextBox(90, 140, "", lcd.FONT_DejaVu24, 0xFF0000, rotate=0)
label7 = M5TextBox(90, 160, "", lcd.FONT_DejaVu24, 0xFF0000, rotate=0)   
        
run()