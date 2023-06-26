import sys
import cv2
import numpy as np
import os

sys.path.append(os.path.abspath(os.path.dirname(__file__)))
from dlclive.dlclive import DLCLive
import utils


class DetectMousePose():
    def __init__(self, model_paths):
        """ Using DeepLabCut(DLC), a pose estimation toolbox, to locate the body parts 
        of mouse as they do a whisker-based task """

         # initialize DLCLive
        self.dlcmodels = {}
        for key in model_paths:
            self.dlcmodels[key] = DLCLive(utils.ospath(path = model_paths[key]), display = False)
            self.dlcmodels[key].init_inference()
        print("Successfully initialized DeepLabCut model(s)")


    def run_inference(self, frame, key):
        dlcresults = self.dlcmodels[key].get_pose(np.array([frame]))
        return dlcresults