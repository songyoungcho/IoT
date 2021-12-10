
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
servo2.ChangeDutyCycle(2.5)  # 모터 초기화 0도 열어둔 상태

unlock=True
trunk=False

@app.route("/")
def home():
    return render_template('pro.html')

@app.route("/lock")     #웹에서 차문 잠금 
def lock():                                  
    global unlock
    if unlock==False:     #잠겨있을 때 
        servo.ChangeDutyCycle(2.5)  #모터로 잠금 0도  -->열기
        GPIO.output(led_pin_l,1)    # LED ON
        GPIO.output(led_pin_r,1)    # LED ON
        time.sleep(1)   # 1초동안 대기상태
        GPIO.output(led_pin_l,0)    # LED OFF   # LED 깜빡 
        GPIO.output(led_pin_r,0)    # LED OFF
        unlock = not unlock
        return "unlock"

    else:     #열려있을 때
        servo.ChangeDutyCycle(7.5)  # 모터로 잠금 90도
        GPIO.output(led_pin_l,1)    # LED ON
        GPIO.output(led_pin_r,1)    # LED ON
        time.sleep(1)   # 1초동안 대기상태
        GPIO.output(led_pin_l,0)    # LED OFF   # LED 깜빡 
        GPIO.output(led_pin_r,0)    # LED OFF
        unlock = not unlock
        return "lock"

# try:      #움직임 인식하면 트렁크 열림
#     while True:
#         if GPIO.input(motion) == 1: 	#물체 감지
#             if trunk == False:
#                 servo.ChangeDutyCycle(2.5)    #트렁크 열기
#                 print("motion working")
#                 time.sleep(0.2)
#                 unlock = not unlock
#             else:
#                 servo.ChangeDutyCycle(7.5)    #트렁크 닫기
#                 time.sleep(0.2)
#                 unlock = not unlock

# except KeyboardInterrupt:
#                 print("Stopped by User")
#                 GPIO.cleanup()



if __name__ == "__main__":
    app.run(host="0.0.0.0")