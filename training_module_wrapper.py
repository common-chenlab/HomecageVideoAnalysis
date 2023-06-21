import argparse
import os
import sys
import json
import traceback
import utils
import shutil
import time
import gc

from dlclive.dlclive import DLCLive
from constants import folder_paths, modelinfo
from vatm import TrainingModuleAnalysis
from computervisiontasks.ocr import TimestampOCR
from objectdetection.tm_dlc_detection import DetectTMwDLC
from mousecoatrecognition import MouseCoatRecognitionTM
from slackpython import SendSlackNotification


def get_args():
    """ gets arguments from commnad line """
    parser = argparse.ArgumentParser(
        description="Parsing arugment for video path",
        epilog="python file.py -s WFR4F4EF151EF86E4_9_5"
    )
    # required argument
    parser.add_argument("--json_file_name", '-jfn', required=False, help='name of json file with video paths.')
    parser.add_argument("--task_array", '-ta', required=False, help='boolean to determine script is submitted as job aray or single job')
    args = parser.parse_args()
    return args.json_file_name, args.task_array


if __name__ == '__main__':

    json_file_name, task_array = get_args()

    # load in JSON file
    f = open(json_file_name)
    data = json.load(f)
    f.close()

    if task_array == "1":
        task_id = int(os.environ["SGE_TASK_ID"])
        video_path_list = data[task_id-1]
    else:
        video_path_list = data[0]

    # update video paths based on current operating system
    video_path_list = [utils.ospath(path = video_path) for video_path in video_path_list]

    # move video files to scratch folder if on scc
    if sys.platform == 'linux':
        video_path_list = utils.move_videos_2_scc_scratch(video_path_list = video_path_list)

    # initialize mouse coat recognition model
    mousecoatrecognition = MouseCoatRecognitionTM(model_path = utils.ospath(path = modelinfo['coatrecognition']))

    # training module DLC model
    tmdetectionmodel = DetectTMwDLC(model_path = utils.ospath(modelinfo['tmdetection']))

    # initialize tesserocr (optical character recognition) model
    ocr = TimestampOCR(camera_view = 'TM', model_path = utils.ospath(path = modelinfo['ocr']))

    # mouse DLC models
    dlc_model_paths = modelinfo['dlctm']['model_paths']

    # initialize DLCLive
    dlcmodels = {}
    for key in dlc_model_paths:
        dlcmodels[key] = DLCLive(utils.ospath(path = dlc_model_paths[key]), display = False)
        dlcmodels[key].init_inference()
    print("Successfully initialized DeepLabCut model(s)")

    # run through all videos in list
    for video_path in video_path_list:
        va_object = None
        print('\n')
        try:
            va_object = TrainingModuleAnalysis(video_path = video_path, dlcmodels = dlcmodels, ocr = ocr, 
                mousecoatrecognition = mousecoatrecognition, tmdetectionmodel = tmdetectionmodel)
            va_object.run()

            del va_object
        except:
            if va_object:
                # catch any exceptions when running video analysis
                va_object.log_error()
            else:
                print("Error during initialization of video analysis for {}".format(os.path.basename(video_path)))
                traceback.print_exc()
        gc.collect()

    # after completion, close all models used
    for key in dlcmodels:
        dlcmodels[key].close()
    print("Complete.")
    sys.exit()
