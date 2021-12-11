
import RPi.GPIO as GPIO
import threading
import time
from tkinter import *  
import spidev
from flask import Flask, request
from flask import render_template

app = Flask(__name__)

led_pin_l = 21
led_pin_r = 2
SERVO_PIN = 13
SERVO_PIN2 = 19
motion = 6

# 불필요한 warning 제거, GPIO핀의 번호 모드 설정
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
# GPIO 18번 핀을 출력으로 설정
GPIO.setup(led_pin_l, GPIO.OUT)
GPIO.setup(led_pin_r, GPIO.OUT)
GPIO.setup(SERVO_PIN, GPIO.OUT)
GPIO.setup(SERVO_PIN2, GPIO.OUT)
GPIO.setup(motion, GPIO.IN)

print ("PIR Ready . . . . ")
time.sleep(5)  # PIR 센서 준비 시간 

# PWM 인스턴스 servo 생성, 주파수 50으로 설정 
servo = GPIO.PWM(SERVO_PIN,50)
servo2 = GPIO.PWM(SERVO_PIN2,50)
# PWM 듀티비 0 으로 시작 
servo.start(0)
servo.ChangeDutyCycle(2.5)  # 모터 초기화 0도 열어둔 상태
servo2.start(0)
servo2.ChangeDutyCycle(7.5)  # 모터 초기화 0도 열어둔 상태

delay = 0.5
# MCP3008 채널설정
sw_channel = 0
vrx_channel = 1
vry_channel = 2
# SPI 인스턴스 spi 생성
spi = spidev.SpiDev()
# SPI 통신 시작하기
spi.open(0, 0)
# SPI 통신 속도 설정
spi.max_speed_hz = 100000


unlock=True
trunk=False
open=False

# 0 ~ 7 까지 8개의 채널에서 SPI 데이터를 읽어서 반환
def readadc(adcnum):
    if adcnum > 7 or adcnum < 0:
        return -1
    r = spi.xfer2([1, 8 + adcnum << 4, 0])
    data = ((r[1] & 3) << 8) + r[2]
    return data

@app.route("/")
def home():
    return render_template('login.html')

@app.route("/pro")
def main():
    return render_template('pro.html')

@app.route("/pro/drive")
def main():
    return render_template('drive.html')



@app.route("/lock")     #웹에서 차문 잠금 
def lock():               
        servo.ChangeDutyCycle(7.5)  # 모터로 잠금 90도
        GPIO.output(led_pin_l,1)    # LED ON
        GPIO.output(led_pin_r,1)    # LED ON
        time.sleep(1)   # 1초동안 대기상태
        GPIO.output(led_pin_l,0)    # LED OFF   # LED 깜빡 
        GPIO.output(led_pin_r,0)    # LED OFF

        return "lock"

@app.route("/unlock")
def unlock():
    servo.ChangeDutyCycle(2.5)  #모터로 잠금 0도  -->열기
    GPIO.output(led_pin_l,1)    # LED ON
    GPIO.output(led_pin_r,1)    # LED ON
    time.sleep(1)   # 1초동안 대기상태
    GPIO.output(led_pin_l,0)    # LED OFF   # LED 깜빡 
    GPIO.output(led_pin_r,0)    # LED OFF
    return "unlock"


#트렁크 버튼
@app.route("/trunk")
def trunk():
    global trunk
    if trunk==False:
        servo2.ChangeDutyCycle(2.5)  #모터로 잠금 0도  -->닫기
        trunk=not trunk
        return "trunkclose"
        
    else:
        servo2.ChangeDutyCycle(7.5)  #모터로 잠금 0도  -->열기
        trunk=not trunk
        return "trunkopen"


if __name__ == "__main__":
    app.run(host="0.0.0.0")