import cv2
from dlclive.dlclive import DLCLive
import numpy as np
import os
import utils

class DetectMousePose():
	def __init__(self, model_paths):
		""" Using DeepLabCut(DLC), a pose estimation toolbox, to locate the body parts 
		of mouse as they do a whisker-based task """

		    # initialize DLCLive
    self.dlcmodels = {}
    for key in model_paths:
        dlcmodels[key] = DLCLive(utils.ospath(path = model_paths[key]), display = False)
        dlcmodels[key].init_inference()
    print("Successfully initialized DeepLabCut model(s)")


    def run_inference(self, frame, key):
    	height, width = frame.shape[1]
    	dlcresults = self.dlcmodels[key].get_pose(np.aray([frame]))
    	return dlcresults