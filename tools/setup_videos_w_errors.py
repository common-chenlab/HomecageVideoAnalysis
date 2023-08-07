import datetime
import os
import glob
import json
import shutil
import time
s
# NOTE: Only run on local Windows machine that has BlueIris installed

""" Video analysis may fail sometimes due to glitches when converting from BVR to MP4 using ffmpeg.
These glitches can cause the timestamps to be distorted etc. 
To fix this, we can export to MP4 using BlueIris directly instead of ffmpeg on the SCC

This script will copy the BVR files located in <video_folder> into a new folder called <error_folder>. 
Then, it will create a json file with the list of videos to re-run analysis on """

if __name__ == "__main__":
    
    # location to where the BVR files are located
    video_folder = r"V:\Projects\Homecage\BlueIrisVideos\TrainingModule6"
    
    # location to where to copy BVR videos with errors (Repair/Regenerate BlueIris db after copying clips)
    error_copy_folder = r"C:\BlueIris\VideoswErrors"
    
    # create new error folder
    os.makedirs(error_copy_folder, exist_ok=True)

    # get folders that errored. Folder names correspond to video file name
    video_names_w_errors_list = glob.glob(os.path.join(r"Z:\Projects\Homecage\DLCVideos\trainingmodule_errors", "TM_*.*_*"))
    
    videos_w_errors_copied_for_json = []
    for errored_video in video_names_w_errors_list:
    	video_file_name = os.path.basename(errored_video)
    	video_file_path = os.path.join(video_folder, video_file_name + ".bvr")

    	if not os.path.exists(video_file_path):
    		print("Video file does not exist:", video_file_path)
    	else:
            print("Copied", os.path.basename(video_file_path))
            shutil.copy2(video_file_path, error_copy_folder)
            videos_w_errors_copied_for_json.append([video_file_path])          
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
        print("Copy/make sure this json file is in the HomecageVideoAnalysis json folder.")
        print("Command to run on SCC:\nqsub -t 1-{} training_module_job.sh scc/jsons/{}".format(str(len(videos_w_errors_copied_for_json)),
                                                                             os.path.basename(json_file_path)))
    else:
        print("No json file created.")