#!/usr/bin/env python
import cv2
from picamera import PiCamera
from picamera.array import PiRGBArray
import argparse
import time
import RPi.GPIO as GPIO
import threading

# Pin in use
pinlight = 5
pinlight2 = 21
pinlightbol = 11
led = 4
capteur = 18
bpmanuel = 12
bpplateau = 17
direction = 13   # Direction GPIO Pin
step = 19  # Step GPIO Pin
en_sl = 26 # Enable and Sleep (turn on driver)

dirpl = 23
steppl = 22
sprpl = 10
en_slpl = 24

mode = (6, 16, 20)   # Microstep Resolution GPIO Pins
resolution = {'Full': (0, 0, 0),
              'Half': (1, 0, 0),
              '1/4': (0, 1, 0),
              '1/8': (1, 1, 0),
              '1/16': (0, 0, 1),
              '1/32': (1, 0, 1)}

cw = 0     # Clockwise Rotation
ccw = 1    # Counterclockwise Rotation

stepccw = 25
stepcw = 100

cwpl = 1
ccwpl = 0

#delay = .0208 / 32
delay = .002
y = 1
res = 6
#etape = SPR / 12


# waiting value between each motor rotation sequence
vitesse = 0.001 #waiting

nbcroquettes = 0

# define board value
etape = []
# define global number for increment photos taken
num = 0

# initialize the camera and grab a reference to the raw camera capture
camera = PiCamera()
camera.resolution = (640, 480)
#camera.framerate = 16
camera.vflip = True
camera.hflip = True
rawCapture = PiRGBArray(camera, size=(640, 480))

# allow the camera to warmup
time.sleep(0.1)

# construct the argument parse and parse the arguments
ap = argparse.ArgumentParser()

ap.add_argument("-i", "--info",
    default="/home/pi/camera/photos/info.info",
    help="file info pixel count")

ap.add_argument("-c", "--cascade",
    default="/home/pi/camera/xmlfile/cascade3.xml",
    help="path to cat detector haar cascade")
args = vars(ap.parse_args())

detector = cv2.CascadeClassifier(args["cascade"])

fileinfo = open(args["info"], "w")



def setup():
	GPIO.setmode(GPIO.BCM)
	GPIO.setup(pinlight, GPIO.OUT, initial = GPIO.LOW)
	GPIO.setup(pinlight2, GPIO.OUT, initial = GPIO.LOW)
	GPIO.setup(pinlightbol, GPIO.OUT, initial = GPIO.LOW)
	GPIO.setup(capteur,GPIO.IN, pull_up_down=GPIO.PUD_UP)
	GPIO.setup(led,GPIO.OUT)
	GPIO.setup(bpmanuel,GPIO.IN, pull_up_down=GPIO.PUD_UP)
	GPIO.setup(bpplateau,GPIO.IN, pull_up_down=GPIO.PUD_UP)
	GPIO.setup(direction, GPIO.OUT)
	GPIO.setup(step, GPIO.OUT)
	GPIO.setup(en_sl, GPIO.OUT)
	GPIO.setup(steppl, GPIO.OUT)
	GPIO.setup(dirpl, GPIO.OUT)
	GPIO.setup(mode, GPIO.OUT)
	GPIO.setup(en_slpl, GPIO.OUT)
	GPIO.output(en_slpl, GPIO.LOW)


def rotation_screw(dir, stp):
	GPIO.output(direction, dir)
	for x in range(stp):
		GPIO.output(step, GPIO.HIGH)
		time.sleep(vitesse)
		GPIO.output(step, GPIO.LOW)
		time.sleep(vitesse)

#  define rotation sequences of screw
def serving():
	GPIO.output(en_sl, GPIO.HIGH)
	GPIO.output(mode, resolution['Full'])
	rotation_screw(ccw,stepccw)
	time.sleep(0.5)
	GPIO.output(mode, resolution['Full'])
	rotation_screw(cw,stepcw)
	GPIO.output(en_sl, GPIO.LOW)

class closer(threading.Thread):

    def __init__(self):
        threading.Thread.__init__(self)
        self.resume = True
        self.pause_cond = threading.Condition(threading.Lock())

    def run(self):

        while True:
            while self.resume:
                if GPIO.input(bpplateau) == 1:
                    closing()
        time.sleep(0.1)

    def pause(self):
        self.resume = False
        self.pause_cond.acquire()

    def running(self):
        self.resume = True
        self.pause_cond.notify()
        self.pause_cond.release()


def closing():
	step_count = 0
	GPIO.output(en_slpl, GPIO.HIGH)
	GPIO.output(dirpl, cwpl)
	while GPIO.input(bpplateau) == 1 and step_count < 1000:
		GPIO.output(mode, resolution['1/16'])
		GPIO.output(steppl, GPIO.HIGH)
		time.sleep(delay)
		GPIO.output(steppl, GPIO.LOW)
		time.sleep(delay)
		step_count += 1
	GPIO.output(en_slpl, GPIO.LOW)

def opening():
    GPIO.output(en_slpl, GPIO.HIGH)
    GPIO.output(dirpl, ccwpl)
    step_count = 0
    while step_count < 225:
        GPIO.output(mode, resolution['1/8'])
        GPIO.output(steppl, GPIO.HIGH)
        time.sleep(delay)
        GPIO.output(steppl, GPIO.LOW)
        time.sleep(delay)
        step_count += 1
    GPIO.output(en_slpl, GPIO.LOW)

def detect():
    global num
    loop = 0
    loop2 = 0
    for frame in camera.capture_continuous(rawCapture, format="bgr", use_video_port=True):
        image = frame.array
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        rects = detector.detectMultiScale(gray, scaleFactor=1.3, minNeighbors=20, minSize=(60, 95))
        # if detect
        if rects < "[":
            loop = loop + 1
            print "detected"
            rawCapture.truncate(0)
        # otherwise increment loop value
        else :
            loop2 = loop2 + 1
            loop = 0
            print "not detected"
            rawCapture.truncate(0)
        # if detect complet: take the framing of detection (rects[0]) , convert to black and white and count the number of white pixel
        if loop == 1:
            x, y, w, h = rects[0]
            img = image[y:(y+h),x:(x+w)]
            num += 1
            imgpath = ("/home/pi/camera/photos/imageok%s.png"%num)
            imgnb = ("/home/pi/camera/photos/nb%s.png"%num)
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
    x = 185
    y = 310
    h = 165
    w = 210
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

# define GPIO state
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
        ir()
		#thread
        t_closing = closer()
        t_closing.start()
        t_closing.pause()

        print('Ready!')
        while True:
            if GPIO.input(bpmanuel) == 0:
                opening()
                nbcroquettes = countcroquettes()
                print nbcroquettes
                closing()



            time.sleep(0.01)
            if GPIO.input(capteur) == 0:
                t_closing.running()
                light()
                if detect() and nbcroquettes > 31000:
					lightoff()
					t_closing.pause()
					opening()
					serving()
					monaeating()
					nbcroquettes = countcroquettes()
					closing()
                elif detect() and nbcroquettes < 31000:
					lightoff()
					t_closing.pause()
					opening()
					monaeating()
					nbcroquettes = countcroquettes()
					closing()
                else:
				    t_closing.pause()
				    lightoff()


            time.sleep(0.01)


    except KeyboardInterrupt:
        GPIO.cleanup()
