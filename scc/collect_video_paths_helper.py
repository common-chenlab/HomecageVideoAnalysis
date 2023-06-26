import argparse
import json
import os
import subprocess
import datetime
import sys

sys.path.append('../')
import utils


def get_args():
    """ gets arguments from commnad line """
    parser = argparse.ArgumentParser(
        description="Parsing arugment for video path",
        epilog="python file.py -s WFR4F4EF151EF86E4_9_5"
    )
    # required argument
    parser.add_argument("--video_folder_path", '-vfp', required=True, help='path to directory with video files.')
    parser.add_argument("--rig_list", '-rl', nargs="+", required=True, help='list of rigs to run analysis on.')
    args = parser.parse_args()
    return args.video_folder_path, args.rig_list



if __name__ == "__main__":
    VIDEO_FOLDER_PATH, rig_num_list = get_args()

    # print arguments used
    print("video_folder_path={}".format(VIDEO_FOLDER_PATH))
    print("rig_num_list={}".format(rig_num_list))

    # convert string integers to just integers
    rig_num_list = [int(i) if i.isdigit() else i for i in rig_num_list]

    parselist = True
    if rig_num_list[0] == "all":
        parselist = False

    # file extensions to look for (eg. ".mp4")
    fileext = '.mp4'

    # number of video paths to run analysis in each job
    batch_size = 10

    # get full list of videos
    print("Reading files from directory ...")
    complete_video_path_list = [os.path.join(VIDEO_FOLDER_PATH, video_filename) for video_filename in os.listdir(VIDEO_FOLDER_PATH) if fileext in video_filename]
    print("Number of files in entire folder:", len(complete_video_path_list))
    # filtered list of videos
    video_path_list = []

    if parselist:
        print("Parsing list of video paths ...")
        for video_path in complete_video_path_list:
            file_info = utils.parse_filename(filename = os.path.basename(video_path))
            # check if video path is in rig number selection list
            if file_info['rig_no'] in rig_num_list:
                video_path_list.append(video_path)
    else:
        print("Using full directory ...")
        video_path_list = complete_video_path_list
    del complete_video_path_list

    # separate list of videos in chunks
    video_list_chunked = [video_path_list[i*batch_size:(i+1)*batch_size] for i in range((len(video_path_list)+batch_size-1)//batch_size)]

    # save list to JSON file
    # note: file is always saved as videolist.json
    json_obj = json.dumps(video_list_chunked)

    # create jsons directoru
    json_folder = os.path.join(os.getcwd(), "jsons")
    os.makedirs(json_folder, exist_ok=True)

    # create json file name 
    # TODO: make this more customizable, adding timestamp, rig numbers in json for more details on the video paths ...
    json_file_name = 'video_file_list_{}.json'.format(str(batch_size))

    json_file_path = os.path.join(json_folder, json_file_name)
    with open(json_file_path, "w") as outfile:
        outfile.write(json_obj)
    print("{} created.".format(json_file_path))

    num_of_jobs = len(video_list_chunked)

    # number of paths in json
    print('Number of video paths in json:', len(video_path_list))
    print('Number of chunks with batch_size={}: {}'.format(str(batch_size), str(num_of_jobs)))

    # create path to log folder
    log_folder = os.path.join(os.getcwd(), "log")
    os.makedirs(log_folder, exist_ok=True)

    # submit job
    subprocess.run(["qsub", 
        "-t", "1-{}".format(str(num_of_jobs)), 
        "-tc", "50", 
        "-o", log_folder,
        "-e", log_folder,
        "training_module_job.sh", 
        json_file_path, 
        "task_array"
    ])
