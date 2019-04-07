#!/usr/bin/env python
import RPi.GPIO as GPIO

# Pin in use
bpplateau = 17
direction = 13   # Direction GPIO Pin
step = 19  # Step GPIO Pin
en_sl = 26 # Enable and Sleep (turn on driver)

dirpl = 23
steppl = 22
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
stepcw = 150

cwpl = 1
ccwpl = 0

# waiting value between each motor rotation sequence
vitesse = 0.001 #waiting
#delay = .0208 / 32
delay = .002


def setup():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(bpplateau,GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(direction, GPIO.OUT)
    GPIO.setup(step, GPIO.OUT)
    GPIO.setup(en_sl, GPIO.OUT)
    GPIO.setup(steppl, GPIO.OUT)
    GPIO.setup(dirpl, GPIO.OUT)
    GPIO.setup(mode, GPIO.OUT)
    GPIO.setup(en_slpl, GPIO.OUT)
    GPIO.output(en_slpl, GPIO.LOW)
    GPIO.output(en_sl, GPIO.LOW)

def rotation_screw(dir, stp):
	GPIO.output(direction, dir)
	for x in range(stp):
		GPIO.output(step, GPIO.HIGH)
		time.sleep(vitesse)
		GPIO.output(step, GPIO.LOW)
		time.sleep(vitesse)

#  define rotation sequences of screw
def serving():
	print("serving")
	GPIO.output(en_sl, GPIO.HIGH)
	rotation_screw(ccw,stepccw)
	time.sleep(0.5)
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
		GPIO.output(mode, resolution['1/8'])
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


def helloworld():
    print("hello")
