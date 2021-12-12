import RPi.GPIO as GPIO
import threading
import time
from tkinter import *  
import spidev
from flask import Flask, request
from flask import render_template, render_template, Response 
from PIL import Image
import picamera

app = Flask(__name__)
led_pin_l = 21
led_pin_r = 2
SERVO_PIN = 13
SERVO_PIN2 = 19
motion = 6
buzzer=18
TRIG = 23
ECHO = 24
warning=26
# 불필요한 warning 제거, GPIO핀의 번호 모드 설정
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
# GPIO 18번 핀을 출력으로 설정
GPIO.setup(led_pin_l, GPIO.OUT)
GPIO.setup(led_pin_r, GPIO.OUT)
GPIO.setup(SERVO_PIN, GPIO.OUT)
GPIO.setup(SERVO_PIN2, GPIO.OUT)
GPIO.setup(motion, GPIO.IN)
GPIO.setup(buzzer, GPIO.OUT)
GPIO.setup(TRIG,GPIO.OUT)
GPIO.setup(ECHO,GPIO.IN)
GPIO.setup(warning, GPIO.OUT)
# PWM 인스턴스 servo 생성, 주파수 50으로 설정 
servo = GPIO.PWM(SERVO_PIN,50)
servo2 = GPIO.PWM(SERVO_PIN2,50)
p = GPIO.PWM(buzzer, 100)  
GPIO.output(TRIG, False)
# print("Waiting for sensor to settle")
# time.sleep(2)
# PWM 듀티비 0 으로 시작 
servo.start(0)
servo2.start(0)

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
picture=False

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
        return "trunkopen"
        
    else:
        servo2.ChangeDutyCycle(7.5)  #모터로 잠금 0도  -->열기
        trunk=not trunk
        return "trunkclose"
x=0
y=0
def gearLoop():
    global x,y
# 무한루프
# X, Y 축 포지션값
    vrx_pos = readadc(vrx_channel)
    vry_pos = readadc(vry_channel)
# 스위치 입력
    sw_val = readadc(sw_channel)
# 출력
    if(vrx_pos==0):
        x=x-1
    if(vrx_pos>900):
        x=x+1
    if(vry_pos==0):
        y=y-1
    if(vry_pos>800):
        y=y+1
    if(x>1 or x<-1):
        x=0
    if(y<0 or y>3):
        y=0
    if(sw_val==0):
        p.start(10)
        time.sleep(3)
        p.stop()
    time.sleep(0.5)
    return x,y
a,b=gearLoop()

def distance():
    GPIO.output(TRIG, True)   # Triger 핀에  펄스신호를 만들기 위해 1 출력
    time.sleep(0.00001)       # 10µs 딜레이 
    GPIO.output(TRIG, False)
        
    while GPIO.input(ECHO)==0:
        start = time.time()	 # Echo 핀 상승 시간 
    while GPIO.input(ECHO)==1:
        stop= time.time()	 # Echo 핀 하강 시간 
            
    check_time = stop - start
    distance = check_time * 34300 / 2
    time.sleep(0.4)	# 0.4초 간격으로 센서 측정 
    return distance
@app.route('/warn')
def warn():
    if distance()<20:
        p.start(10)
        GPIO.output(warning,1)
        time.sleep(3)
        GPIO.output(warning,0)
        p.stop()
    if distance()<10:
        p.start(20)
        GPIO.output(warning,1)
        time.sleep(2)
        GPIO.output(warning,0)
        p.stop()
    if distance()<5:
        p.start(30)
        GPIO.output(warning,1)
        time.sleep(1)
        GPIO.output(warning,0)
        p.stop()
@app.route('/gear')
def gear():
    # t=threading.Thread(target=gearc)
    # t.start()
    t1=threading.Thread(target=warn)
    t1.start()
    a,b=gearLoop()
    x=''
    y=''
    #a,b=gearLoop()
    if(a==-1):
        x='l'
        GPIO.output(led_pin_l,1)    # LED ON
        time.sleep(1)   # 1초동안 대기상태
        GPIO.output(led_pin_l,0)    # LED OFF   # LED 깜빡 
    if(a==0):
        x='x'
        
    if(a==1):
        x='r'
        GPIO.output(led_pin_r,1)    # LED ON
        time.sleep(1)   # 1초동안 대기상태
        GPIO.output(led_pin_r,0)    # LED OFF   # LED 깜빡 
    if(b==0):
        y='d'
    if(b==1):
        y='n'
    if(b==2):
        y='b'
    if(b==3):
        y='p'
    print(x+y)
    time.sleep(0.3)
    return x+y





if __name__ == "__main__":
    app.run(host="0.0.0.0")