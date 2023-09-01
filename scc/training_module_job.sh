#!/bin/bash -l

#this merges output and error files into one file
#$ -j y

#this sets the project for the script to be run under
#$ -P jchenlab

#number of cores to select
#$ -pe omp 16

#specify the time limit
#$ -l h_rt=12:00:00

#activate conda environment
module load miniconda
conda activate VideoAnalysisENV

#handle hdf5 files on scc
export HDF5_USE_FILE_LOCKING='FALSE'

#make sure Tensorflow doesn't exceed the number of cores used
export TF_NUM_INTEROP_THREADS=$(( $NSLOTS - 1 ))
export TF_NUM_INTRAOP_THREADS=1

slptime=$(echo "scale=4 ; ($RANDOM/32768) * 10" | bc)
sleep $slptime

if [ $2 = "task_array" ]; then
	task_array="1"
else
	task_array="0"
fi

#run main python script
cd ..
python training_module_wrapper.py --json_file_name $1 --task_array $task_array