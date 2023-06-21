#!/bin/bash -l

#specify array job
#$ -t 1-1

#this makes it so you'll get an email at the (b)eginning of the job, (e)nd of the job, and on an (a)bort of the job
#$ -m ea

#this merges output and error files into one file
#$ -j y

#this sets the project for the script to be run under
#$ -P jchenlab

#$ -pe omp 16

#Specify the time limit
#$ -l h_rt=12:00:00

#activate conda environment
module load miniconda
conda activate VideoAnalysisENV

#temporary solution to deal with h5 files
HDF5_USE_FILE_LOCKING='FALSE'

#run main python script
python maincv.py
