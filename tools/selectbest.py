#!/usr/bin/env python
import cv2
import os
import argparse
import progressbar
import re

path = '/home/pi/robot/photos/_nb/'
files = []

info = open("/home/pi/robot/photos/info.dat", "a")
bg = open("/home/pi/robot/photos/bg.txt", "a")

# construct the argument parse and parse the arguments
ap = argparse.ArgumentParser()

ap.add_argument("-c", "--cascade",
            default="/home/pi/robot/xmlfile/cascade3.xml")
args = vars(ap.parse_args())

detector = cv2.CascadeClassifier(args["cascade"])

def detect():
    good = wrong = i = 0
  
    for r, d, f in os.walk(path):
        for file in f:
           files.append(os.path.join(r, file))
           cpt = sum([len(files)])
        
        widgets = ['\x1b[33mProgress\x1b[39m', progressbar.Percentage(),
                               progressbar.Bar(marker='\x1b[32m#\x1b[39m')]
        #bar.start()
        with progressbar.ProgressBar(widgets=widgets, max_value=cpt) as bar:
           for f in files:
               image = cv2.imread(f, cv2.IMREAD_UNCHANGED)
               gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
               rects = detector.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=14)
               bar.update(i+1)
               i += 1
               if len(rects):
                   #print("detected")
                   good += 1
                   result = "%s" % (rects)
                   sub_rects= re.sub('[^0-9 ]+','',result)
                   insert = "%s  1 %s\n" % (f,sub_rects)
                   info.write(insert)               
               else :
                   #print("not detected")
                   wrong += 1
                   bg_insert = "%s\n" % (f)
                   bg.write(bg_insert)

    percent = ((cpt - wrong) / cpt) * 100
    print(" good found=",good)
    print(" wrong found=",wrong)
    print(" percent=",percent)

if __name__ == '__main__':
    try:
        detect()
    except KeyboardInterrupt:
        exit()
