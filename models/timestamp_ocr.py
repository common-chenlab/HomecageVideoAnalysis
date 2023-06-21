import cv2
import datetime
import numpy as np
from PIL import Image
import re
import tesserocr
import time

class TimestampOCR():
	def __init__(self, camera_view, model_path):
		""" Object that holds the Tesserocr(optical character recognition) api to run on timestamps for each frame """

		# depending on the camera view, the timestamp is slighly in a different location in frame ( these are hardcoded positions of the timestamp based on camera GUI [RevoTech])
		if camera_view == 'TM':
			self.ocrposition = [0.74, 0.98, 0.962, 0.995] # position of timestamp in TM view (minx, maxx, miny, maxy)
		elif camera_view == 'CV':
			self.ocrposition = [0.75, 1.0, 0.965, 1.0] # position of timestamp in CV view (minx, maxx, miny, maxy)
		else:
			raise ValueError("camera_view doesn't match enumerate (TM, CV)")

		# initialize tesserocr api
		# path = r"C:\Users\Abed\OneDrive\Documents\tesstrain/data/", 
		self.tess_api = tesserocr.PyTessBaseAPI(
			path = model_path, 
			lang="ts_fast", 
			oem = tesserocr.OEM.LSTM_ONLY
		)

		self.tess_api.SetVariable("tessedit_char_whitelist", "0123456789: ")

		# allocate previous data variables to save for later
		self.prev_frame = np.array([])
		self.prev_timestamp = {"text_from_img": None, "datetime_object": None}
		print('Successfully loaded in Tesserocr API!\n')


	def process_frame(self, frame):
		""" crop frame to only view timestamp in frame, create threshold ostu for more distinguishable numbers in timestamp frame """

		# double-check if image has 3 channels, if so convert to grayscale
		if frame.ndim == 3:
			frame = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)

		# crop frame to only view timestamp
		# note: change accordingly if position of timestamp changes! currently position of timestamp in videos/live feed are static
		height, width = frame.shape[:2]

		frame = frame[int(height*self.ocrposition[2]):int(height*self.ocrposition[3]), int(width*self.ocrposition[0]):int(width*self.ocrposition[1])]

		# manually remove backslashes '/' from image
		height, width = frame.shape[:2]

		# delete the backslashes
		frame[:, 18:25] = 0
		frame[:, 42:49] = 0
		frame = np.delete(frame, np.s_[18:25], axis=1)  
		frame = np.delete(frame, np.s_[34:41], axis=1)  

		# implement threshold to generate binary image
		ret, frame = cv2.threshold(frame, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

		# adding border
		height, width = frame.shape[:2]
		top = int(0.8 * frame.shape[0])  # shape[0] = rows
		bottom = top
		left = int(0.1 * frame.shape[1])  # shape[1] = cols
		right = left
		frame = cv2.copyMakeBorder(frame, top, bottom, left, right, cv2.BORDER_CONSTANT, None, [255,255,255])

		# save previous processed frame for next ocr
		if self.prev_frame.size == 0:
			self.prev_frame = frame
			run_ocr = True
		else:
			# element-wise subtraction to find pixel different between current and previous frame
			sub_frame = np.absolute(frame - self.prev_frame)
			
			# save current as previous
			self.prev_frame = frame

			# if different > 0, timestamp has changed and ocr will run
			run_ocr = True if sub_frame.sum() > 0 else False

		# convert to Pillow for ocr
		frame = Image.fromarray(frame)

		return frame, run_ocr


	def raw_inference(self, frame, process_frame = False):
		""" run ocr on frame without checking string results """

		if process_frame:
			# process frame
			frame, _ = self.process_frame(frame = frame)

		# run tesserocr
		self.tess_api.SetImage(frame)
		text_from_img = self.tess_api.GetUTF8Text()

		return text_from_img


	def run_inference(self, frame, DEBUG = False): 
		""" run opticial character recognition (Tesseract) on frame to detect timestamp """

		# prepare frame for ocr(tesseract)
		frame, run_ocr = self.process_frame(frame = frame)
		
		if run_ocr:

			if DEBUG: # display cropped timestamp in debug mode
				height, width = np.array(frame).shape[:2]
				cv2.imshow('DEBUG(tesserocr) {}x{}'.format(height, width), np.array(frame))
				cv2.waitKey(0)

			# run tesserocr
			self.tess_api.SetImage(frame)

			text_from_img = self.tess_api.GetUTF8Text()

			# parse string predicted and convert to datetime object
			datetime_object = self.parse_timestamp(timestamp = text_from_img)
			self.prev_timestamp = {"text_from_img": text_from_img, "datetime_object": datetime_object}

		else:
			text_from_img = self.prev_timestamp["text_from_img"]
			datetime_object = self.prev_timestamp["datetime_object"]


		# in DEBUG mode, print results for each frame
		if DEBUG:
			print('Word confidences:', self.tess_api.AllWordConfidences())
			print('Tesserocr predicted:', text_from_img)
			print('\n')

		return datetime_object


	def parse_timestamp(self, timestamp):
		""" parse predicted string from tesserocr. expected format example: 03/10/2022 11:50:21 (MM/DD/YYYY HH:MM:SS)
		UPDATE: (1/27/2023) The "/" seems to be causing issues with a few digits (0, 9). Hardcode removing the back slashes from the image when processing """

		# remove leading and trailing spaces in prediction
		timestamp = timestamp.strip()

		# double-check if timestamp predicted was blank
		if timestamp == "":
			# return -1 to use previous timestamp
			return -1

		# remove characters not present in list
		known_character_list = ['0','1','2','3','4','5','6','7','8','9',':',' ']
		temp_timestamp = timestamp
		for char in temp_timestamp:
			if char not in known_character_list:
				timestamp = timestamp.replace(char, '')

		# restricted format of timestamp
		ts_pattern = re.compile(pattern = "^([0-1]*[1-9] *[0-3][0-9] *20[0-9][0-9]) *([0-2][0-9]:[0-5][0-9]:[0-5][0-9])$")
		match_object = ts_pattern.fullmatch(string = timestamp)

		# check if pattern exists in string
		if match_object:
			datestr = str(match_object[1]).strip()
			timestr = str(match_object[2]).strip()
		else:
			raise ValueError("Incorrect format of timestamp:", timestamp)

		# month, day, year = [int(num) for num in datestr.split(' ')]
		# UPDATE: different way of parsing DATE
		datestrdigits = datestr.replace(" ", "")
		month, day, year = int(datestrdigits[:2]), int(datestrdigits[2:4]), int(datestrdigits[4:])
		hour, minute, second = [int(num) for num in timestr.split(':')]

		# TODO: Future work to change timestamp to millisecond precision
		# no millisecond precision yet, hardcoding to 0
		millisecond = 0

		datetime_object = datetime.datetime(year = year, month = month, day = day, hour = hour, minute = minute,
										 second = second, microsecond = millisecond * 1000) 
		return datetime_object


	def get_timestamp_offset(self, init, curr):
		""" get offset between current datetime(current_timestamp) and initial datetime(init_timestamp)  """

		# get datetime difference
		diff = curr - init

		# get difference in seconds
		diff_in_secs = diff.total_seconds()

		return diff_in_secs
