import RPi.GPIO as GPIO
import Adafruit_Nokia_LCD as LCD
import Adafruit_GPIO.SPI as SPI
import cgitb; cgitb.enable()
import spidev 
import PIL
import time
import math
import json
import requests
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont

url = 'http://itfactorydries.hub.ubeac.io/iotessdrieaugustyns'
uid = 'iotessdriesaugustyns'

GPIO.setmode(GPIO.BCM)

GPIO.setup(16, GPIO.OUT) # Motor
GPIO.setup(19, GPIO.OUT) # Motor
GPIO.setup(20, GPIO.OUT) # Motor
GPIO.setup(26, GPIO.OUT)  # Motor
GPIO.setup(12, GPIO.IN)  # Ultrasonic sensor
GPIO.setup(13, GPIO.OUT) # Ultrasonic sensor

spi = spidev.SpiDev() 
spi.open(0,0) 
spi.max_speed_hz = (1000000)

DC = 23
RST = 24
SPI_PORT = 0
SPI_DEVICE = 1

disp = LCD.PCD8544(DC, RST, spi=SPI.SpiDev(SPI_PORT, SPI_DEVICE, max_speed_hz=4000000))
image = Image.new('1', (LCD.LCDWIDTH, LCD.LCDHEIGHT))
disp.begin(contrast=50)
font = ImageFont.load_default()
draw = ImageDraw.Draw(image)

def ultra():
    GPIO.output(13, 1)
    time.sleep(0.0001)
    GPIO.output(13, 0)

    while GPIO.input(12) == 0:
        pass
    signalhigh = time.time()
    while GPIO.input(12) == 1:
        pass
    signallow = time.time()
    passed = signallow - signalhigh
    distance = passed * 17000
    return round(distance, 0) 

def map(value, start1, stop1, start2, stop2):
    return round(start2 + (stop2 - start2) * ((value - start1) / (stop1 - start1)),0) 

def readadc(adcnum): 
    if ((adcnum > 7) or (adcnum < 0)):
        return -1
    r = spi.xfer2([1,(8+adcnum)<<4,0]) 
    adcout = ((r[1]&3) << 8) + r[2] 
    return adcout
    
def turn_up():
    GPIO.output(26, 0)
    GPIO.output(16, 1)
    GPIO.output(19,1)
    time.sleep(0.002)
    GPIO.output(16, 0)
    GPIO.output(20, 1)  
    time.sleep(0.002)
    GPIO.output(19, 0)
    GPIO.output(26, 1)
    time.sleep(0.002)
    GPIO.output(20, 0)
    GPIO.output(16, 1)
    time.sleep(0.002)
    
def turn_down():
    GPIO.output(16, 0)
    GPIO.output(26, 1)
    GPIO.output(20,1)
    time.sleep(0.002)
    GPIO.output(26, 0)
    GPIO.output(19, 1)  
    time.sleep(0.002)
    GPIO.output(20, 0)
    GPIO.output(16, 1)
    time.sleep(0.002)
    GPIO.output(19, 0)
    GPIO.output(26, 1)
    time.sleep(0.002)

if __name__ == "__main__":
    while True:
        dist = ultra()
        tmp0 = readadc(0)
        req_dist = map(tmp0, 0, 1023, 3, 31)
        dist_star = map(dist, 3, 31, 0, 14)
        req_dist_star = map(req_dist, 3, 31, 0, 14)
        print("Current height:")
        print(dist)
        print("Required height:")
        print(req_dist)
        draw.rectangle((0, 0, LCD.LCDWIDTH, LCD.LCDHEIGHT), outline=255, fill=255)
        draw.text((1, 0), "Current height:", font=font)
        draw.text((1, 8), str(dist), font=font)
        draw.text((1, 16), "*"*int(dist_star), font=font)
        draw.text((1, 24), "Desired height:", font=font)
        draw.text((1, 32), str(req_dist), font=font)
        draw.text((1, 40), "*"*int(req_dist_star), font=font)
        disp.image(image)
        disp.display()
        if dist < req_dist:
            #Platform too low
            turn_up()
        elif dist > req_dist:
            #Platform too high
            turn_down()
        else:
            #Platform on required distance
            data = {
                "id": uid,
                 "sensors": [{
                    "id": "adc channel0",
                      "data": dist,
                  }]
            }
            r = requests.post(url, verify=False, json=data)