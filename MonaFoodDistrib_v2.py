#!/usr/bin/env python
import cv2
from picamera import PiCamera
from picamera.array import PiRGBArray
import argparse
import time
import RPi.GPIO as GPIO
import pymysql
import robotic


# Pin in use
pinlight = 5
pinlight2 = 21
pinlightbol = 11
led = 4
ledtank = 21
capteur = 18
capteurtank = 2
bpmanuel = 12


nbcroquettes = 0

# define global number for increment photos taken
num = 0
imgnb = ''

# initialize the camera and grab a reference to the raw camera capture
camera = PiCamera()
camera.resolution = (640, 480)
#camera.framerate = 16
camera.vflip = True
camera.hflip = True
rawCapture = PiRGBArray(camera)

# allow the camera to warmup
time.sleep(0.1)

# construct the argument parse and parse the arguments
ap = argparse.ArgumentParser()

ap.add_argument("-c", "--cascade",
    default="/home/pi/robot/xmlfile/cascade3.xml")
args = vars(ap.parse_args())

detector = cv2.CascadeClassifier(args["cascade"])


def setup():
	GPIO.setmode(GPIO.BCM)
	GPIO.setup(pinlight, GPIO.OUT, initial = GPIO.LOW)
	GPIO.setup(pinlight2, GPIO.OUT, initial = GPIO.LOW)
	GPIO.setup(pinlightbol, GPIO.OUT, initial = GPIO.LOW)
	GPIO.setup(capteurtank,GPIO.IN, pull_up_down=GPIO.PUD_UP)
	GPIO.setup(ledtank,GPIO.OUT)
	GPIO.setup(capteur,GPIO.IN, pull_up_down=GPIO.PUD_UP)
	GPIO.setup(led,GPIO.OUT)
	GPIO.setup(bpmanuel,GPIO.IN, pull_up_down=GPIO.PUD_UP)


def detect():
    global num
    loop = 0
    loop2 = 0
    for frame in camera.capture_continuous(rawCapture, format="bgr", use_video_port=True):
        image = frame.array
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        rects = detector.detectMultiScale(gray, scaleFactor=1.3, minNeighbors=15, minSize=(60, 95))

        # if detect
        print("startdetect")
        print(rects)
        if len(rects):
            loop = loop + 1
            print("detected")
            rawCapture.truncate(0)
        # otherwise increment loop value
        else :
            loop2 = loop2 + 1
            loop = 0
            print("not detected")
            rawCapture.truncate(0)
        # if detect complet: take the framing of detection (rects[0]) , convert to black and white and count the number of white pixel
        if loop == 1:
            x, y, w, h = rects[0]
            img = image[y:(y+h),x:(x+w)]
            num += 1
            imgpath = ("/home/pi/robot/photos/imageok%s.png"%num)
            imgnb = ("/home/pi/robot/photos/nb%s.png"%num)
            # Save image and write black pixel info
            cv2.imwrite(imgpath ,image)
            cv2.imwrite(imgnb ,img)
            rawCapture.truncate(0)
            return True
            break
        if loop2 == 5:
            return False
            break

def monaeating():
    e = 0
    while e!=1:
        if GPIO.input(capteur) == 0:
            time.sleep(5)
            # mona mange is eating
        elif GPIO.input(capteur) == 1:
            e = 1
            # mona finished to eat

def countcroquettes():
    x = 205
    y = 310
    h = 165
    w = 200
    light()
    time.sleep(1)
    for frame in  camera.capture_continuous(rawCapture, format="bgr", use_video_port=True):
        image = frame.array
        img = image[y:(y+h),x:(x+w)]
        nb = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        ret,thresh = cv2.threshold(nb,160,255, cv2.THRESH_BINARY)
        whitep = cv2.countNonZero(thresh)
        rawCapture.truncate(0)
        lightoff()
        break
    return whitep

def write_db(request,imgnb,serv_state,nbcroquettes,access):
    connection = pymysql.connect(host='localhost',
                                user='monastat',
                                password='passmona',
                                db='routine_mona',
                                charset='utf8mb4',
                                cursorclass=pymysql.cursors.DictCursor)
    try:
        with connection.cursor() as cursor:
            if request == "openning":
                sql = "INSERT INTO daily_food (`photo_number`,`open_time`,`serving_added`,`nb_pixels`,`access`) VALUES (%s,NOW(),%s,%s,%s);"
                cursor.execute(sql,(imgnb,serv_state,nbcroquettes,access))
            elif request == "tankmanagement":
                sql = "INSERT INTO tank (`sac_number`) VALUES (1);"
                cursor.execute(sql)
            else:
                cursor.execute("SELECT id FROM daily_food ORDER BY id DESC LIMIT 0, 1")
                lastid = cursor.fetchone()
                sql = "UPDATE daily_food SET `close_time`=NOW(),`nb_pixels`=%s WHERE id =%s;"
                cursor.execute(sql,(nbcroquettes,lastid['id']))
    finally:
        connection.commit()
        connection.close()

def tankmanagement():
    GPIO.output(ledtank, GPIO.HIGH)
    if GPIO.input(capteurtank) == 1:
	    write_db('tankmanagement','','','','')
    GPIO.output(ledtank, GPIO.LOW)

def light():
    GPIO.output(pinlight,GPIO.HIGH)
    GPIO.output(pinlight2,GPIO.HIGH)
    GPIO.output(pinlightbol,GPIO.HIGH)

def lightoff():
    GPIO.output(pinlight,GPIO.LOW)
    GPIO.output(pinlight2,GPIO.LOW)
    GPIO.output(pinlightbol,GPIO.LOW)

def ir():
    GPIO.output(led, GPIO.HIGH)

if __name__ == '__main__':
    try:
        setup()
        robotic.setup()
        ir()
		#thread
        t_closing = robotic.closer()
        t_closing.start()
        t_closing.pause()

        print('Ready!')
        while True:
            if GPIO.input(bpmanuel) == 0:
                robotic.opening()
                robotic.serving()
                robotic.closing()



            time.sleep(0.01)
            if GPIO.input(capteur) == 0:
                t_closing.running()
                light()
                if detect() and nbcroquettes > 30000:
                    lightoff()
                    t_closing.pause()
                    robotic.opening()
                    robotic.serving()
                    write_db('openning',imgnb,'1','','1')
                    monaeating()
                    nbcroquettes = countcroquettes()
                    robotic.closing()
                    write_db('','','',nbcroquettes,'')
                elif detect() and nbcroquettes < 30000:
                    lightoff()
                    t_closing.pause()
                    robotic.opening()
                    monaeating()
                    write_db('openning',imgnb,'0','','1')
                    nbcroquettes = countcroquettes()
                    robotic.closing()
                    write_db('','','',nbcroquettes,'')
                else:
                    t_closing.pause()
                    lightoff()
                    #write_db('insert','','0',nbcroquettes,'0')


            time.sleep(0.01)


    except KeyboardInterrupt:
        GPIO.cleanup()
