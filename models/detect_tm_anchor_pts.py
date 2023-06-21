import cv2
from dlclive.dlclive import DLCLive
import numpy as np
import os
import utils


class DetectTMAnchorPts():
	def __init__(self, model_path, CONFIDENCE_THRESH=0.5):
		""" Using DeepLabCut(DLC), a pose estimation toolbox, to locate the 
		anchor points of the training module in camera view """

		if not os.path.isdir(model_path):
			raise ValueError(f'Weights path "{model_path}" does not point to a file.')

		self.model = DLCLive(model_path, display = False)
		self.model.init_inference()
		self.CONFIDENCE_THRESH = CONFIDENCE_THRESH
		print('Successfully loaded in DetectTMwDLC model!\n')


	def run_inference(self, frame):
		height, width = frame.shape[:2]

		# convert frame to 3-channel grayscale
		gsframe = cv2.cvtColor(frame.copy(), cv2.COLOR_BGR2GRAY)
		gsframe = cv2.cvtColor(gsframe, cv2.COLOR_GRAY2RGB)

		dlcresults = self.model.get_pose(np.array([gsframe]))

		# most important tm_markers are 0 and 8
		if dlcresults[0,2] < self.CONFIDENCE_THRESH or dlcresults[8,2] < self.CONFIDENCE_THRESH:
			return None

		# if more than 2 markers are with low likelihood
		if np.sum(dlcresults[:,2] < self.CONFIDENCE_THRESH) >= 2:
			return None

		# hardest tm_marker to measure
		if dlcresults[5,2] < self.CONFIDENCE_THRESH:
			if dlcresults[2,2] > self.CONFIDENCE_THRESH and dlcresults[3,2] > self.CONFIDENCE_THRESH and dlcresults[6,2] > self.CONFIDENCE_THRESH:
				x_delta = dlcresults[3,0] - dlcresults[2,0]
				y_delta = dlcresults[3,1] - dlcresults[2,1]
				dlcresults[5,0] = dlcresults[6,0] + x_delta
				dlcresults[5,1] = max(0, dlcresults[6,1] + y_delta + 5)
				dlcresults[5,2] = -1.0	
			else:
				return None

		xmin, xmax = int(min(dlcresults[:, 0])), int(max(dlcresults[:, 0]))
		ymax = int(max(dlcresults[:, 1]))
		xwidth = min(xmax-xmin, 400)
		yheight = ymax-0
		original_tm_position = (xmin/width, 0, xwidth/width, yheight/height)

		padding_for_aspect_ratio = utils.resize_cropped_frame(position = original_tm_position, max_width = width, 
			max_height = height, aspect_ratio = 400/300)

		return {'dlc_marker_positions': dlcresults, 
			'original_tm_position': original_tm_position, 'padding_for_aspect_ratio': padding_for_aspect_ratio}
