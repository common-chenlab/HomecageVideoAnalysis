from chenlabpylib import chenlab_filepaths
import cv2
import datetime
import gc
import math
import numpy as np
import os
import pandas as pd
from scipy.io import savemat
import shutil
import sys
import stat
import time
import traceback
import utils

from paths import folder_paths, modelinfo, led_issue_info
from models.led_tracker import led_status_check, led_movement_check
from models.detect_objects import get_object_location


class TrainingModuleAnalysis():
    def __init__(self, video_path, mouseposemodels, ocr, mousecoatrecognition, tmdetectionmodel):
        """ object for data analysis  """

        # full path to video file
        self.video_path = video_path

        # check path to video file
        if not os.path.isfile(self.video_path):
            raise ValueError('Video path {} does not point to a file.'.format(os.path.basename(self.video_path)))

        self.video_file_name = os.path.basename(self.video_path)[:-4]
        if self.video_file_name[-2:] == "_1":
            self.video_file_name = self.video_file_name[:-2]

        # path to deeplabcut models
        self.dlc_model_paths = modelinfo['dlctm']['model_paths']

        # body parts to track
        self.body_parts = modelinfo['dlctm']['body_parts']

        # path to save mat files
        self.mat_folder = chenlab_filepaths(path=folder_paths['matfiletm'])

        # path to error folder
        self.error_folder = chenlab_filepaths(path=folder_paths['errortm'])

        # deeplabcut models
        self.mouseposemodels = mouseposemodels

        # ocr object
        self.ocr = ocr

        # mouse coat recognition model object
        self.mousecoatrecognition = mousecoatrecognition

        # maskrcnn object
        self.tmdetectionmodel = tmdetectionmodel

        self.dlc_total_time = 0

    def init_video_data(self):
        """ initialize video data """

        # open video file using cv2
        self.cap = cv2.VideoCapture(self.video_path)

        # check if video cap opened successfully
        if not self.cap.isOpened():
            raise IOError('Video {} could not be opened; it may be corrupted.'.format(os.path.basename(self.video_path)))
        else:
            print('Video {} successfully loaded!'.format(os.path.basename(self.video_path)))

        # extract information from file name
        file_info = utils.parse_filename(filename=self.video_file_name)

        # get camera detials
        self.training_module_id = file_info['rig_no']  # ex: (1, 2, 3, 4, 5, 6, 7, ... )

        # use csv file with trial datetimes instead of relying the LED
        if self.training_module_id in led_issue_info['rig_led_issues']:
            self.rig_trial_dt_csv_path = chenlab_filepaths(path=led_issue_info['led_issue_csv_paths'][self.training_module_id])
            self.use_trial_csv = True
        else:
            self.rig_trial_dt_csv_path = None
            self.use_trial_csv = False

        self.camera_view = file_info['camera_view']  # camera view = enum("TM", "CV")
        self.videodatetime = file_info['datetime']
        self.CAMERA_NAME = self.camera_view + "_" + str(self.training_module_id)  # CAMERA_NAME EX: TM_1, TM_2 ...

        # location to save generated trial .mat files
        self.mat_subfolder_path = utils.create_mat_subfolder(videofilename=self.video_file_name, training_module_id=self.training_module_id,
                                                             camera_view=self.camera_view, videodatetime=self.videodatetime, cageID="")

        # get metadata of video file
        self.get_metadata()

        # initilaize object detection
        self.init_object_detection()

    def get_metadata(self):
        """ get metadata from video file """

        self.fps = round(self.cap.get(cv2.CAP_PROP_FPS))  # average video fps
        self.resolution = (int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)))  # (width, height)
        # estimate number of frames in video
        self.video_frame_count = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        # keep track of frame index throughout video
        self.frame_idx = -1

    def init_object_detection(self):
        """ find first frame that can locate needed objects for analysis """

        while True:
            ret, frame = self.cap.read()

            if ret:
                self.frame_idx += 1

                # if skipped over 100 frames (10 seconds of video), must be an issue with video, skip for now
                if self.frame_idx > 100:
                    raise ValueError('Unable to find needed objects in video after {} frames. Skipping video ...'.format(self.frame_idx))

                # process frame
                rgbframe = self.process_frame(frame.copy())

                # note: position of objects are normalized based on frame resolution
                gsframe = cv2.cvtColor(rgbframe, cv2.COLOR_RGB2GRAY)
                self.led_position = get_object_location(gsframe.copy(), 'LED', confidence_thresh=0.8)

                # go to next frame if no LED detected in current frame
                if self.led_position is None:
                    print('No LED detected in frame-idx={}, skipping to next ...'.format(self.frame_idx))
                    continue

                # run maskrcnn to get training module position
                tm_detection = self.tmdetectionmodel.run_inference(frame=rgbframe.copy())

                # go to next frame if no TM detected in current frame
                if tm_detection is None:
                    print('No TM detected in frame-idx={}, skipping to next ...'.format(self.frame_idx))
                    continue

                # segmentation results
                self.tm_dlc_position = tm_detection['dlc_marker_positions']
                self.original_tm_position = tm_detection['original_tm_position']
                self.padding_for_aspect_ratio = tm_detection['padding_for_aspect_ratio']

                print('ALL objects detected in frame-idx={} for video!'.format(self.frame_idx))
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, self.frame_idx)
                self.frame_init_cutoff = self.frame_idx
                self.frame_idx -= 1
                self.prev_frame = frame
                break
            else:
                raise ValueError('Unable to find needed objects in any frame(frame-idx={}), skipping video ...'.format(self.frame_idx))
                break

    def close(self):
        """ close session """
        self.cap.release()  # release video capture
        # delete video if copied to compute node scratch folder
        if sys.platform == 'linux' and 'scratch' in self.video_path:
            os.remove(self.video_path)
        print("Closing", datetime.datetime.now())

    def process_frame(self, frame):
        """ preprocess frames to fit training module analysis requirements """
        frame = cv2.resize(frame, (640, 360))
        rgbframe = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        return rgbframe

    def run_dlc(self, frame):
        """ run deeplabcut model inference """
        height, width = frame.shape[:2]

        # crop frame for dlc inference
        x, y, w, h = self.original_tm_position
        x, y, w, h = int(x*width), int(y*height), int(w*width), int(h*height)
        frame = frame[y:y+h, x:x+w]

        if self.padding_for_aspect_ratio[0] == 'y':
            frame = cv2.copyMakeBorder(frame, self.padding_for_aspect_ratio[1], 0, 0, 0, cv2.BORDER_CONSTANT)  # height padding
        elif self.padding_for_aspect_ratio[0] == 'x':
            frame = cv2.copyMakeBorder(frame, 0, 0, 0, self.padding_for_aspect_ratio[1], cv2.BORDER_CONSTANT)  # width padding

        # Mouse pose DLC model was trained on 400x300 dim frames
        frame = cv2.resize(frame, (400, 300))

        # mouse pose prediction
        dlcmarkers = self.mouseposemodels.run_inference(frame=frame, key=self.TRIALDATA['mousecoatcolor']['prediction'])
        return dlcmarkers

    def run_coat_recognition(self, frame):
        """ run mouse coat recognition model """
        height, width = frame.shape[:2]

        # crop frame for dlc inference
        x, y, w, h = self.original_tm_position
        x, y, w, h = int(x*width), int(y*height), int(w*width), int(h*height)
        frame = frame[y:y+h, x:x+w]

        if self.padding_for_aspect_ratio[0] == 'y':
            frame = cv2.copyMakeBorder(frame, self.padding_for_aspect_ratio[1], 0, 0, 0, cv2.BORDER_CONSTANT)  # height padding
        elif self.padding_for_aspect_ratio[0] == 'x':
            frame = cv2.copyMakeBorder(frame, 0, 0, 0, self.padding_for_aspect_ratio[1], cv2.BORDER_CONSTANT)  # width padding

        # DLC model was trained on 400x300 dim frames
        frame = cv2.resize(frame, (400, 300))

        # predict mouse coat color
        mousecoatpredicted, confidence = self.mousecoatrecognition.run_inference(frame=frame)
        return mousecoatpredicted, confidence

    def init_trial_data(self, frame, frame_idx):
        """ initialize data for trial
        return encoding
         0 = successful initialization
        -1 = unsuccessful initialization but continuing attempt to initialize
        -2 = unsuccessful initialization of entire trial
        """

        # initialize trial information
        self.TRIALDATA = {
            'raw_data': os.path.basename(self.video_path),  # basename of video file used
            'training_module_id': self.training_module_id,
            'camera_view': self.camera_view,
            'resolution': self.resolution,
            'fps': self.fps,
            'dlcdata': [],  # deeplabcut data
            'dlc_processed': 0,  # whether pose estimation was run
            'marker_list': self.body_parts,  # list of labeled markers tracked
            'tm_markers': self.tm_dlc_position,  # position of markers for tm
            'timestamp_per_frame': [],  # timestamp for each frame in trial
            'led_position': self.led_position,  # position of led in frame
            'edge_case': 0,  # whether trial occurred at the beginning or end of video
            'frame_indices': [],  # list of frame indices used in video for trial
        }

        # get timestamp of frame
        ocr_predicted = self.ocr.run_inference(frame=frame.copy())
        if ocr_predicted == -1:  # Skipping this frame since no timestamp was recognized in initial frame
            print('Timestamp of frame is blank. Cannot get initial trial timestamp. Skipping to next frame.')
            return -1

        # ignore trial entirely if starting trial_datetime is before 9:32AM (CILSE white light on till 9:30AM) or after 9:30PM
        if (ocr_predicted.time() < datetime.time(hour=9, minute=32, second=00)) or (ocr_predicted.time() > datetime.time(hour=21, minute=28, second=00)):
            return -2

        # save trial datetime
        self.TRIALDATA['trial_datetime'] = ocr_predicted.strftime('%m/%d/%Y, %H:%M:%S')

        # predict coat of mouse in frame
        mousecoatpredicted, confidence = self.run_coat_recognition(frame=frame.copy())

        # save mouse coat color and DLC model to be used
        self.TRIALDATA['mousecoatcolor'] = {'prediction': mousecoatpredicted, 'confidence': confidence}
        self.TRIALDATA['dlc_model_path'] = self.dlc_model_paths[mousecoatpredicted]

        print('--- START OF NEW TRIAL ---')
        print('mouse coat predicted as {} with confidence {}'.format(self.TRIALDATA['mousecoatcolor']['prediction'],
                                                                     round(self.TRIALDATA['mousecoatcolor']['confidence'], 4)))
        print('initial trial datetime:', self.TRIALDATA['trial_datetime'])
        print('frame-idx={}'.format(self.frame_idx))
        return 0

    def end_trial(self):
        """ end trial and save data to file """

        # process data collected from trial
        self.process_trial_data()

        # save trial data to .mat file
        self.save_to_matfile()

        # reset trial data and call garbage collection
        self.TRIALDATA = {}
        gc.collect()
        print('----- END OF TRIAL -----\n')

    def camera_view_unstable(self, frame):
        """ if camera view was blocked or accidentally moved, rerun led and tm detection """

        rgbframe = self.process_frame(frame.copy())
        if self.led_position:
            framedifferencing = led_movement_check(frame, self.prev_frame, self.led_position)  # check if led position has moved
            if framedifferencing > 50:
                # ignore if change is just a switch in LED status
                prev_LED_status = led_status_check(frame=self.process_frame(self.prev_frame.copy()), led_position=self.led_position)
                curr_LED_status = led_status_check(frame=rgbframe.copy(), led_position=self.led_position)
                if prev_LED_status != curr_LED_status:  # camera view interference is due to LED status change
                    self.prev_frame = frame.copy()
                    return False
                print("Camera view interference in frame-idx={}. Difference jump = {}. Re-running object detection.".format(self.frame_idx, framedifferencing))
                self.led_position = get_object_location(cv2.cvtColor(rgbframe.copy(), cv2.COLOR_RGB2GRAY), 'LED', confidence_thresh=0.8)
                if self.led_position is None:
                    print("No LED detected in frame-idx={}, skipping to next frame...".format(self.frame_idx))
                    return True
                else:
                    tm_detection = self.tmdetectionmodel.run_inference(frame=rgbframe.copy())
                    if tm_detection is None:
                        print('LED detected but no TM detected in frame-idx={}, skipping to next frame...'.format(self.frame_idx))
                        return True
                    else:
                        self.tm_dlc_position = tm_detection['dlc_marker_positions']
                        self.original_tm_position = tm_detection['original_tm_position']
                        self.padding_for_aspect_ratio = tm_detection['padding_for_aspect_ratio']
                        self.prev_frame = frame.copy()
                        print("Objects re-detected in frame-idx={}".format(self.frame_idx))
                        return False
            else:
                self.prev_frame = frame.copy()
                return False
        else:
            self.led_position = get_object_location(cv2.cvtColor(rgbframe.copy(), cv2.COLOR_RGB2GRAY), 'LED', confidence_thresh=0.8)
            if self.led_position is None:
                print("No LED detected in frame-idx={}, skipping to next frame...".format(self.frame_idx))
                return True
            else:
                tm_detection = self.tmdetectionmodel.run_inference(frame=rgbframe.copy())
                if tm_detection is None:
                    print('LED detected but no TM detected in frame-idx={}, skipping to next frame...'.format(self.frame_idx))
                    return True
                else:
                    self.tm_dlc_position = tm_detection['dlc_marker_positions']
                    self.original_tm_position = tm_detection['original_tm_position']
                    self.padding_for_aspect_ratio = tm_detection['padding_for_aspect_ratio']
                    self.prev_frame = frame.copy()
                    print("Objects re-detected in frame-idx={}".format(self.frame_idx))
                    return False

    def run_analysis(self, BATCH_OF_FRAMES, edge_case=0):
        """ using BATCH_OF_FRAMES, run video analysis (DLC, OCR, ...) """

        # initialize trial
        init_successful = False
        for i in range(len(BATCH_OF_FRAMES)):
            # time.sleep(0.1)
            frame, frame_idx = BATCH_OF_FRAMES[i]
            status_code = self.init_trial_data(frame=frame, frame_idx=frame_idx)
            if status_code == 0:  # success
                init_idx = i
                init_successful = True
                break
            elif status_code == -2:  # end trial early
                del self.TRIALDATA
                return

        if init_successful is False:  # unable to successfully initialize trial
            print("Unable to sucessfully initialize trial at started in frame-idx={}".format(BATCH_OF_FRAMES[0][1]))
            del self.TRIALDATA
            return

        self.TRIALDATA['edge_case'] = 1 if init_idx == self.frame_init_cutoff else edge_case  # check if trial is edge_case

        # OCR inference
        for i in range(init_idx, len(BATCH_OF_FRAMES)):
            # time.sleep(0.1)
            frame, frame_idx = BATCH_OF_FRAMES[i]
            ocr_predicted = self.ocr.run_inference(frame=frame.copy())  # run OCR
            if ocr_predicted == -1:  # use previous timestamp if ocr is blank in frame or if timestamp in wrong format
                if i == init_idx:
                    raise ValueError("Problem initializing trial for frame-idx={}".format(i))
                print('No timestamp recognized in frame. Using previous frame as timestamp ...')
                ocr_predicted = self.TRIALDATA['timestamp_per_frame'][-1]
            self.TRIALDATA['timestamp_per_frame'].append(ocr_predicted)

        start_time_dlc = time.time()
        # DLC inference
        prev_dlc_frame, _ = BATCH_OF_FRAMES[init_idx]
        for i in range(init_idx, len(BATCH_OF_FRAMES)):
            # time.sleep(0.1)
            frame, frame_idx = BATCH_OF_FRAMES[i]
            # run DLC: use previous frames dlc results if frame difference is less than 5 pixels (mouse hasn't moved or TM is empty)
            dlcmarkers = self.TRIALDATA['dlcdata'][-1] if ((cv2.absdiff(frame[:, :, 0], prev_dlc_frame[:, :, 0]).sum() < 5) and (i != init_idx)) else self.run_dlc(frame=frame.copy())
            self.TRIALDATA['dlc_processed'] = 1
            self.TRIALDATA['dlcdata'].append(dlcmarkers)
            self.TRIALDATA['frame_indices'].append(frame_idx)  # append frame index
            prev_dlc_frame = frame.copy()

        end_time_dlc = time.time() - start_time_dlc
        self.dlc_total_time += end_time_dlc

        self.end_trial()

    def run(self):
        """ run through entire video """

        # retrieve initial video data
        self.init_video_data()

        # use trial file for runnning analysis instead of relying on LED
        if self.use_trial_csv:
            self.run_with_trial_file()
            return

        # initialize start time
        start_time = time.time()

        # active trial status
        self.active_trial = False

        # corrupted trial status
        self.corrupt_status = False

        # batch of frames for trial
        BATCH_OF_FRAMES = []

        while True:
            ret, frame = self.cap.read()

            if ret:
                # time.sleep(.005)
                self.frame_idx += 1

                # check if camera view is stable while no trial is occuring
                if self.active_trial is False:
                    is_camera_unstable = self.camera_view_unstable(frame=frame)
                    if is_camera_unstable is True:
                        continue
                    # time.sleep(0.005)

                # process raw frame
                rgbframe = self.process_frame(frame=frame.copy())

                # get status of led
                led_status = led_status_check(frame=rgbframe.copy(), led_position=self.led_position)

                # run analysis if led status == 1 ("on")
                if (led_status == 1) and (self.corrupt_status is False):
                    self.active_trial = True
                    BATCH_OF_FRAMES.append([rgbframe, self.frame_idx])

                    # trial is corrupt (ex. labview crashed)
                    if len(BATCH_OF_FRAMES) > (self.fps*20):
                        BATCH_OF_FRAMES = []
                        self.corrupt_status = True
                        self.active_trial = False
                else:
                    self.corrupt_status = False
                    self.active_trial = False
                    if len(BATCH_OF_FRAMES) > 0:
                        self.run_analysis(BATCH_OF_FRAMES)
                    BATCH_OF_FRAMES = []
            else:
                if len(BATCH_OF_FRAMES) > 0:  # video ends before trial (edge_case = 1)
                    self.run_analysis(BATCH_OF_FRAMES, edge_case=1)
                    BATCH_OF_FRAMES = []

                # end time of analysis
                total_time = str(datetime.timedelta(seconds=int(time.time() - start_time)))
                print('Elapsed time:', total_time)
                print('DLC time', self.dlc_total_time)
                self.close()
                break

    def run_with_trial_file(self):
        """ run through entire video using csv file with trial data """

        # read csv file for trial data
        # column names ["trial_datetime", "session_datetime", "report_time", "direction_1", "direction_2"]
        df_trial_data = pd.read_csv(self.rig_trial_dt_csv_path, header=0)
        trial_data_list = df_trial_data.values.tolist()

        # subsample and get +-1 hour range of trial timestamps
        min_search_dt, max_search_dt = self.videodatetime - datetime.timedelta(hours=1), self.videodatetime + datetime.timedelta(hours=2)
        filtered_trial_data_list = []
        for trial_data in trial_data_list:
            trial_dt = datetime.datetime.strptime(trial_data[0][:-4], "%Y-%m-%d %H:%M:%S")
            if min_search_dt <= trial_dt <= max_search_dt:
                filtered_trial_data_list.append(trial_data)

        # sort list by datetime in ascending order
        filtered_trial_data_list = sorted(filtered_trial_data_list, key=lambda x: x[0])

        # if trial was found
        trial_match = False

        # batch of frames
        BATCH_OF_FRAMES = []

        # previous frames timestamp
        prev_ocr_predicted = None

        # initialize start time
        start_time = time.time()

        while True:
            ret, frame = self.cap.read()

            if ret:
                self.frame_idx += 1

                # process raw frame
                rgbframe = self.process_frame(frame=frame.copy())

                # run OCR
                ocr_predicted = self.ocr.run_inference(frame=rgbframe.copy())

                # skip if ocr is invalid
                if ocr_predicted == -1:
                    continue

                if trial_match is False:
                    if prev_ocr_predicted == ocr_predicted:
                        # no need to search if timestamp is the same
                        pass
                    else:
                        prev_ocr_predicted = ocr_predicted
                        # TODO: Improve - Brute force linear search through all timestamps
                        for trial_data in filtered_trial_data_list:
                            trial_dt = datetime.datetime.strptime(trial_data[0][:-4], "%Y-%m-%d %H:%M:%S")
                            if ocr_predicted == trial_dt:
                                # number of frames to run analysis on (record_time = lenght of time in ms led is on)
                                recording_time_sec = int(trial_data[2]) / 1000.0  # convert to sec
                                num_of_frames_for_trial = math.ceil(recording_time_sec * self.fps)  # get num of frames (round up always)
                                trial_match = True
                                BATCH_OF_FRAMES = []
                                break

                if trial_match:
                    if len(BATCH_OF_FRAMES) < num_of_frames_for_trial:
                        BATCH_OF_FRAMES.append([rgbframe, self.frame_idx])
                    else:
                        # analysis
                        self.run_analysis(BATCH_OF_FRAMES)
                        BATCH_OF_FRAMES = []
                        trial_match = False
                else:
                    trial_match = False

            else:
                if len(BATCH_OF_FRAMES) > 0 and trial_match:  # video ends before trial (edge_case = 1)
                    self.run_analysis(BATCH_OF_FRAMES, edge_case=1)
                    BATCH_OF_FRAMES = []
                    trial_match = False

                # end time of analysis
                total_time = str(datetime.timedelta(seconds=int(time.time() - start_time)))
                print('Elapsed time:', total_time)
                print('DLC time', self.dlc_total_time)
                self.close()
                break

    def process_trial_data(self):
        """ process the trial data collected before storing as MAT file """

        # convert dlcdata list to numpy array
        self.TRIALDATA['dlcdata'] = np.array(self.TRIALDATA['dlcdata'])

        # convert list of timestamps into a list of offsets (in seconds) from initial trial timestamp
        self.TRIALDATA['timestamp_offset_list'] = [self.ocr.get_timestamp_offset(init=self.TRIALDATA['timestamp_per_frame'][0], curr=ocr_timestamp) for ocr_timestamp in self.TRIALDATA['timestamp_per_frame']]

        # delete 'timestamp_per_frame' key
        del self.TRIALDATA['timestamp_per_frame']

    def save_to_matfile(self):
        """ save results to a single MAT file """

        mat_filename = utils.format_filename(cameraname=self.CAMERA_NAME, datetime_obj=self.TRIALDATA['trial_datetime'], filextension='mat')
        mat_filepath = os.path.join(self.mat_subfolder_path, mat_filename)

        # save trial data to mat file
        savemat(mat_filepath, self.TRIALDATA)

        # allow rw for everyone
        os.chmod(mat_filepath, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)
        print("Saved trial data to {}".format(mat_filename))

    def log_error(self):
        """ log error caught for debugging """

        print("\nError encountered for video", os.path.basename(self.video_path))
        traceback.print_exc()

        # release video capture if open
        try:
            self.cap.release()
        except:
            pass

        # parse filename to locate error folder and mat files created
        file_info = utils.parse_filename(filename=self.video_file_name)

        # get camera identification details
        training_module_id = file_info['rig_no']  # ex: (1, 2, 3, 4, 5, 6, 7, ... )
        camera_view = file_info['camera_view']  # camera view = enum("TM", "CV")
        videodatetime = file_info['datetime']

        # delete mat subfolder with .mat files
        mat_subfolder_path = utils.create_mat_subfolder(self.video_file_name, training_module_id, camera_view, videodatetime)
        if os.path.isdir(mat_subfolder_path):
            shutil.rmtree(mat_subfolder_path)
        else:
            print("MAT subfolder does not exist.")

        # create error subfolder if folder doesn't exit already
        error_subfolder_path = os.path.join(self.error_folder, self.video_file_name)
        if not os.path.isdir(error_subfolder_path):
            os.mkdir(error_subfolder_path)
            os.chmod(error_subfolder_path, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)
        else:
            shutil.rmtree(error_subfolder_path)
            os.mkdir(error_subfolder_path)
            os.chmod(error_subfolder_path, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)
            print("Overriding current error subfolder that exists.")

        # create log file
        log_file_path = os.path.join(error_subfolder_path, "error.log")
        utils.create_logfile(log_file_path=log_file_path)
        os.chmod(log_file_path, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)
