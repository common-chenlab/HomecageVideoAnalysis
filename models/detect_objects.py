import cv2
import numpy as np
import os
from paths import modelinfo
import utils

""" Object Detection used for video analysis
As of 01/12/2021, we are able to detect
	1. Training Module Cage
	2. LED
"""

def get_object_location(img, class_label, confidence_thresh = 0.8, verbose = False, ):
	""" Get initial position of a specific object [class_id]  """
	# NOTE: Set "confidence_thresh" accordingly. Change if needed. Detections are present if prediction is {confidence_thresh} confident

	# check if class_label is valid model, else throw ERROR
	valid_objectdetection_models = ['LED', 'TM']
	if class_label not in valid_objectdetection_models:
		raise ValueError('Error with class_label. {} is not a class id. Ending program ...'.format(class_label))
		return


	############## get model information here. change manually here if needed #################

	# get model information
	model_info = modelinfo['objdetect' + class_label]

	model_folder = utils.ospath(path = model_info['model_folder_path'])
	trained_image_size = model_info['trained_image_size']
	channels = model_info['channels']
	weights_filename = model_info['weights']
	cfg_filename = model_info['config']

	##########################################################################################
		
	# Get dimensions of image
	height, width = img.shape[:2]

	# Check dimensions of input frame match trained frame dimensions
	input_frame_channels = None
	if len(img.shape) == 2:
		input_frame_channels = 1
	elif len(img.shape) == 3:
		input_frame_channels = 3
	else:
		raise ValueError('Issues with input frame for class [{}] for object detection'.format(class_label))

	if input_frame_channels != channels:
		# number of channels trained on is not equal to input frame
		raise ValueError('Number of channels are not the same for class [{}] for object detection'.format(class_label))

	# Config and weights files
	cfg_file = os.path.join(model_folder, weights_filename)
	weights_file = os.path.join(model_folder, cfg_filename)

	# Reading weights and cfg file for object detection model
	net = cv2.dnn.readNet(cfg_file, weights_file)
	classes = [str(class_label)] # LED class detection


	# Getting information of darknet (YOLO_v3)
	layer_names = net.getLayerNames()
	outputLayers = [layer_names[i - 1] for i in net.getUnconnectedOutLayers()]

	# Detecting obj
	blob = cv2.dnn.blobFromImage(img, 0.00392, trained_image_size, (0,0,0), True, crop=False)

	net.setInput(blob)
	outs = net.forward(outputLayers)

	confidences = []
	boxes = []

	for out in outs:
	    for detection in out:
	        scores = detection[5:]
	        class_id = np.argmax(scores)
	        confidence = scores[class_id]

	        # Filter predictions based on confidence threshold
	        if confidence > confidence_thresh:
	            center_x = detection[0] * width
	            center_y = detection[1] * height
	            w, h= detection[2] * width, detection[3] * height
	            x, y = center_x - w /2, center_y - h /2

	            boxes.append([x, y, w, h])
	            confidences.append(float(confidence))

	# Run non-maximum-suppression to ignore overlapping boxes predicted
	indexes = cv2.dnn.NMSBoxes(boxes, confidences, 0.5, 0.4)
	num_object_detected = len(boxes)

	objects_detected = []
	for i in range(num_object_detected):
	    if i in indexes:
	        objects_detected.append([boxes[i], confidences[i]])


	if len(objects_detected) > 0:

		if len(objects_detected) > 1:
			# Issue! More than 1 of the specified objects were detected, choose first index as resort
			if verbose:
				print('More than 1 {} object was detected. {} detected. Using highest confidence prediction.\n'.format(class_label, str(len(objects_detected))))

		# Distribute coordinates
		x, y, w, h = objects_detected[0][0]
		if x < 0:
			x = 0
		if y < 0:
			y = 0

		# Modify coordinates to be with respect to dimensions of width/height ratio
		x, y = x/width, y/height
		w, h = w/width, h/height

		# Get confidence score of object detected
		confidence_score = objects_detected[0][1]

		if verbose:
			print('{} object detected with confidence of {}'.format(class_label, confidence_score))

		# Final predictions with respect to percentage of dimensions of frame
		return (x, y, w, h)

	else:
		if verbose:
			print('{} object not detected in frame.\n'.format(class_label))
		return None