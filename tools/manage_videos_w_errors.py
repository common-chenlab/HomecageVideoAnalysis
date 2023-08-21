import argparse
import datetime
import os
import glob
import json
import shutil
import time
from tqdm import tqdm

# NOTE: Only run on local Windows machine that has BlueIris installed

""" Video analysis may fail sometimes due to glitches when converting from BVR to MP4 using ffmpeg.
These glitches can cause the timestamps to be distorted etc. 
To fix this, we can export to MP4 using BlueIris directly instead of ffmpeg on the SCC

This script will copy the BVR files located in <bvr_video_folder> into a new folder called <copy_folder>. 
Then, it will create a json file with the list of videos in MP4 format to re-run analysis on """


def get_args():
    """ gets arguments from commnad line """
    parser = argparse.ArgumentParser(
        description="Parsing arugment for video path",
        epilog="python file.py -s WFR4F4EF151EF86E4_9_5"
    )
    # arguments
    parser.add_argument("--bvr_video_folder", '-bvrf', required=True, help='path to directory with BVR video files.')
    parser.add_argument("--mp4_video_folder", '-mp4f', required=True, help='path to directory with MP4 video files.')
    parser.add_argument("--copy_error_videos", '-cev', required=False, default=True, help='bool for whether to copy videos with errors to a designated folders.')
    parser.add_argument("--copy_folder", '-cf', required=False, default=None, help='designated folder for where to save videos with errors')
    args = parser.parse_args()
    return args.bvr_video_folder, args.mp4_video_folder, args.copy_error_videos, args.copy_folder



if __name__ == "__main__":

    bvr_video_folder, mp4_video_folder, copy_error_videos, copy_folder = get_args()
    
    # error-check arguments to script
    if copy_error_videos and copy_folder == None:
        raise FileNotFoundError("<copy_folder> should be provided if <copy_error_videos> is True")

    if not os.path.exists(bvr_video_folder):
        raise FileNotFoundError(bvr_video_folder, "was not found.")

    if not os.path.exists(mp4_video_folder):
        raise FileNotFoundError(mp4_video_folder, "was not found.")

    # path to folder with errors (hardcoded for now ... TODO)
    MAIN_ERROR_FOLDER = r"Z:\Projects\Homecage\DLCVideos\trainingmodule_errors"

    if copy_error_videos:
        # create new error folder
        os.makedirs(copy_folder, exist_ok=True)
        progress_str = "Copying videos/Saving to JSON:"
    else:
        progress_str = "Saving to JSON:"

    # get folders that errored. Folder names correspond to video file name
    video_names_w_errors_list = glob.glob(os.path.join(MAIN_ERROR_FOLDER, "TM_*.*_*"))
    print("Number of videos found with errors:", len(video_names_w_errors_list))

    videos_w_errors_copied_for_json = []
    for errored_video in tqdm(video_names_w_errors_list, desc=progress_str):
        video_file_name = os.path.basename(errored_video)

        # BVR BlueIris video format path
        video_file_path_bvr = os.path.join(bvr_video_folder, video_file_name + ".bvr")

        # MP4 video format path
        video_file_path_mp4 = os.path.join(mp4_video_folder, video_file_name + ".mp4")

        if not os.path.exists(video_file_path_bvr):
            print(video_file_path_bvr, "does not exist!")
        else:
            if copy_error_videos:
                shutil.copy2(video_file_path_bvr, copy_folder)
                #print("Copied", os.path.basename(video_file_path_bvr), "to", os.path.basename(copy_folder))

            videos_w_errors_copied_for_json.append([video_file_path_mp4])   
            #print("Saved", os.path.basename(video_file_path_mp4), "to JSON")       
            time.sleep(1)
            
    if videos_w_errors_copied_for_json:
        print("\n")
        json_obj = json.dumps(videos_w_errors_copied_for_json)

        current_dt = datetime.datetime.now().strftime("%m%d%Y%H%M%S")
        json_file_path = "videos_w_errors_{}v_{}.json".format(str(len(videos_w_errors_copied_for_json)), current_dt)
        with open(json_file_path, "w") as outfile:
            outfile.write(json_obj)
           
        print("{} created.".format(json_file_path))
        print("Number of videos with errors(in json):", len(videos_w_errors_copied_for_json)) 
    else:
        print("No json file created.")