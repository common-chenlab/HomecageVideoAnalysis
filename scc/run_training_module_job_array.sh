#!/bin/bash -l

#this merges output and error files into one file
#$ -j y

#this sets the project for the script to be run under
#$ -P jchenlab

#number of cores to select
#$ -pe omp 4

#specify the time limit
#$ -l h_rt=12:00:00

#path to directory with video files
video_folder_path=$1

#shift input arguments
shift

#list of rigs to run anaylsis on in video. set first element in bash array to "all" if plan to run entire directory
rig_num_list=$@

#activate conda environment
module load miniconda
conda activate VideoAnalysisENV

python collect_video_paths_helper.py --video_folder_path $video_folder_path --rig_list $rig_num_list
exit