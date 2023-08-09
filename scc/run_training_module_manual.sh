#!/bin/bash -l

# Use this bash script if you already have a JSON file created to run video analysis
# inputs:
# 	json_file_name: name of the json file. NOTE: make sure this file is in the <jsons> folder
#
# EXAMPLE on how to run: qsub manual_run_scc.sh file.json

#this merges output and error files into one file
#$ -j y

#this sets the project for the script to be run under
#$ -P jchenlab

#number of cores to select
#$ -pe omp 4

#specify the time limit
#$ -l h_rt=12:00:00

#path to json file
json_file_name=$1

#shift input arguments
shift

#(Optional) if you only want to run specific batches in json
task_id_list=("$@")

#create json file path
json_file_path="$PWD/jsons/$json_file_name"

echo "Using JSON file: $json_file_path"

#get number of jobs to run
num_of_jobs=$(jq length $json_file_path)

#get number of videos in json
num_of_videos=$(jq '.[] | length' $json_file_path | awk '{sum+=$0} END{print sum}')

echo "Number of videos in JSON: $num_of_videos"
echo "Number of batches in JSON: $num_of_jobs"

#create log folder if necessary
log_folder="$PWD/log"
mkdir -p $log_folder
chmod -R 777 $log_folder --quiet

if [ "${task_id_list}" ]; then
	echo "Manaully selected task IDs to run: ${task_id_list[@]}"

	for value in "${task_id_list[@]}"
	do
		qsub -t "$value-$value" -tc 50 -o $log_folder -e $log_folder training_module_job.sh $json_file_path task_array
	done
else
	#submit job
	qsub -t "1-$num_of_jobs" -tc 50 -o $log_folder -e $log_folder training_module_job.sh $json_file_path task_array
fi

exit