
import RPi.GPIO as GPIO
import threading
import time
from tkinter import *  
import spidev
from flask import Flask, request
from flask import render_template, render_template, Response 
import cv2
import picamera

app = Flask(__name__)
vc = cv2.VideoCapture(0)

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
record=False

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

@app.route("/drive")
def drive():
    record=True
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

# @app.route("/gear")
# def gear():
#     gear_val=[0,0]
# # 무한루프
#     while True:
# # X, Y 축 포지션값
#         vrx_pos = readadc(vrx_channel)
#         vry_pos = readadc(vry_channel)
# # 스위치 입력
#         sw_val = readadc(sw_channel)
# # 출력
#         if vrx_pos==0:
#                 if gear_val[0]>-1:
#                     gear_val[0]-=1
#                     return gear_val
#         if vrx_pos>1000:
#             if gear_val[0]<1:
#                 gear_val[0]+=1
#                 return gear_val
#         if vry_pos==0:
#             if gear_val[1]>0:
#                 gear_val[1]-=1
#                 return gear_val
#         if vry_pos>1000:
#             if gear_val[1]<3:
#                 gear_val[1]+=1
#                 return gear_val
#         else:
#             return gear_val
# # delay 시간만큼 기다림
#         time.sleep(delay)
#         print(gear_val[0],gear_val[1])

def gearLoop():
    gear_val=[0,0]
# 무한루프
# X, Y 축 포지션값
    vrx_pos = readadc(vrx_channel)
    vry_pos = readadc(vry_channel)
# 스위치 입력
    sw_val = readadc(sw_channel)
# 출력
    if vrx_pos==0:
            if gear_val[0]>-1:
                gear_val[0]-=1
                return gear_val
    if vrx_pos>1000:
        if gear_val[0]<1:
            gear_val[0]+=1
            return gear_val
    if vry_pos==0:
        if gear_val[1]>0:
            gear_val[1]-=1
            return gear_val
    if vry_pos>1000:
        if gear_val[1]<3:
            gear_val[1]+=1
            return gear_val
    else:
        return gear_val

@app.route('/gear')
def gear():
    while(1):
        if(gearLoop()[0]==-1):
            if(gearLoop()[1]==0):
                return "ld"
            if(gearLoop()[1]==1):
                return "ln"
            if(gearLoop()[1]==2):
                return "lr"
            else:
                return "lp"
        if(gearLoop()[0]==0):
            if(gearLoop()[1]==0):
                return "nd"
            if(gearLoop()[1]==1):
                return "nn"
            if(gearLoop()[1]==2):
                return "nr"
            else:
                return "np"
        if(gearLoop()[0]==1):
            if(gearLoop()[1]==0):
                return "rd"
            if(gearLoop()[1]==1):
                return "rn"
            if(gearLoop()[1]==2):
                return "rr"
            else:
                return "rp"


if __name__ == "__main__":
    app.run(host="0.0.0.0")