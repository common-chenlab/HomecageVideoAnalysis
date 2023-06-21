import cv2
import numpy as np
import os

def led_movement_check(frame, prev_frame, led_position, DEBUG = False):
	""" check frame difference between previous and current frame 
	TODO: current logic for checking camera movement can be improved ... 
	"""

	# frame dimensions
	height, width = frame.shape[:2]
	x, y, w, h = led_position
	x, y, w, h = int(x*width), int(y*height), int(w*width), int(h*height)

	prev_frame = prev_frame.copy()[y:y+h, x:x+w]
	frame = frame.copy()[y:y+h, x:x+w]
	og_frame = frame.copy()

	prev_frame = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2HLS)
	frame = cv2.cvtColor(frame, cv2.COLOR_BGR2HLS)

	# set equal lightness channel (avoid change in lighting during video)
	frame[:,:,1] = prev_frame[:,:,1]
	frame[:,:,2] = prev_frame[:,:,2]

	prev_frame = cv2.cvtColor(prev_frame, cv2.COLOR_HLS2BGR)
	frame = cv2.cvtColor(frame, cv2.COLOR_HLS2BGR)

	prev_frame = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY)
	frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

	# normalize frames using min/max
	pfmin, pfmax = np.min(prev_frame), np.max(prev_frame)
	fmin, fmax = np.min(frame), np.max(frame)	
	prev_frame = (prev_frame - pfmin)/(pfmax - pfmin)
	frame = (frame - fmin)/(fmax - fmin)

	framedif = cv2.absdiff(frame, prev_frame)

	mask = framedif.copy()
	mask[framedif>=.05] = 1
	mask[framedif<.05] = 0

	# erode then dilate small noise
	kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2,2))
	mask = cv2.erode(mask, kernel, iterations=2)
	mask = cv2.dilate(mask, kernel, iterations=2)

	pixels_over_thresh = np.sum(mask)

	if DEBUG:
		print("Num of pixels in mask:", pixels_over_thresh)
		cv2.imshow("Camera Movement Process", cv2.hconcat([prev_frame, frame, framedif, mask]))

	return pixels_over_thresh


def led_status_check(frame, led_position, DEBUG = False):
	""" detect current status of LED ('on' or 'off') """

	# LED encoding
	LED_ENCODING = {"ON": 1, "OFF": 0}

	# error check input to function
	if led_position == None:
		raise ValueError('No input for position of LED.')

	if frame.ndim != 3:
		raise ValueError('Input frame must be 3 channels (rgb/bgr).')
		
	# make sure frame dimension is correct
	frame = cv2.resize(frame, (640, 360))

	# frame dimensions
	height, width = frame.shape[:2]

	# unpack LED position coordinates
	x, y, w, h = led_position
	x, y, w, h = int(x*width), int(y*height), int(w*width), int(h*height)

	# crop image to only view LED detected
	frame = frame[y:y+h, x:x+w]

	# frame dimensions of new cropped frame
	height, width = frame.shape[:2]

	# crop image to better focus on only LED
	crop_percentage = 0.15 # must be less than 0.5
	crop_width =  int(width*crop_percentage)
	crop_height = int(height*crop_percentage)

	# consider this the original LED frame to use for methods
	OG_FRAME_ = frame[crop_height:-1*crop_height, crop_width:-1*crop_width]

	# LOGIC: Run green method first for frame. If green method outputs "ON", consider LED == "ON" ...
	# else, attempt pixel method to determine LED status
	LED_STATUS = LED_GREEN_METHOD(frame = OG_FRAME_.copy(), DEBUG = DEBUG)
	
	if LED_STATUS == "ON":
		status = LED_ENCODING[LED_STATUS]
	else:
		# pixel method
		LED_STATUS = LED_PIXEL_METHOD(frame = OG_FRAME_.copy(), DEBUG = DEBUG)
		status = LED_ENCODING[LED_STATUS]

	return status



def LED_GREEN_METHOD(frame, blob_area_threshold = 15,  DEBUG = False):
	### GREEN METHOD: Use green pixels to determine LED status ###

	# use green channel intensity (convert RGB -> HSV)
	framehsv = cv2.cvtColor(frame, cv2.COLOR_RGB2HSV)

	# filter range of HSV values to fit LED color range (green)
	mask = cv2.inRange(framehsv, (30,40,90), (80,255, 255))

	# create binary image that fits mask generated
	green = np.zeros(frame.shape[:2], np.uint8)
	green[mask>0] = 255

	green_before_morph = green.copy()

	# include erosion and dilation to remove any noise that might have not been the LED
	kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2,2))
	green = cv2.erode(green, kernel, iterations=4)
	green = cv2.dilate(green, kernel, iterations = 4)
	green_after_morph = green.copy()

	if DEBUG:
		cv2.imshow('GM_OG_FRAME', frame)
		cv2.imshow('GM_MOD_FRAME', cv2.hconcat([green_before_morph, green_after_morph]))
		cv2.waitKey(1)

	# initialize with "OFF" status, find area of each contour and if contour exceeds threshold, 
	# we assume the LED is "ON" -> set status to "ON" and break from loop, find all available contours (white blobs)
	cnts = cv2.findContours(green, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
	cnts = cnts[0] if len(cnts) == 2 else cnts[1] # quick fix for different opencv2 versions

	LED_STATUS = "OFF"
	for c in cnts:
		area = cv2.contourArea(c)
		if area > blob_area_threshold:
			LED_STATUS = "ON"
			break

	return LED_STATUS



def LED_PIXEL_METHOD(frame, mean_threshold = 250, DEBUG = False):
	### PIXEL METHOD: Using pixel intensity in frame to determine LED status ###

	# FURTHER crop entire image to focus more on center of LED
	height, width = frame.shape[:2]
	crop_percentage = 0.25 # must be less than 0.5
	crop_width =  int(width*crop_percentage)
	crop_height = int(height*crop_percentage)

	framem2 = frame[crop_height:-1*crop_height, crop_width:-1*crop_width] # numpy slicing

	### Use pixel intensity to classify if LED = ON/OFF
	# convert 3-channel image to gryascale w/ opencv
	framem2 = cv2.cvtColor(framem2, cv2.COLOR_RGB2GRAY)

	# get mean of frame
	framem2_mean = framem2.mean(dtype=np.float32)

	if DEBUG:
		print("Mean of LED frame:", framem2_mean)

	# if mean pixel value of frame is >= some threshold, LED is considered "ON"
	if framem2_mean >= mean_threshold:
		LED_STATUS = "ON"
	else:
		LED_STATUS = "OFF"

	return LED_STATUS


