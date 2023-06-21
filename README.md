# Homecage Video Analysis
Using DeepLabCut to precisely track user-defined features of mice as they perform a whisker-based task in a Chen Lab home cage system.

<img src="https://github.com/kevry/HomecageVideoAnalysis/assets/45439265/c2455d7d-cdef-438e-9cc1-256ffa74e7c8" width="300"/>

<img src="https://github.com/kevry/HomecageVideoAnalysis/assets/45439265/a96640ca-1950-4cc6-a994-8ebe4b33098f" width="157"/>

<img src="https://github.com/kevry/HomecageVideoAnalysis/assets/45439265/97efb6e7-2fa9-4cdc-95ae-49d0fb94aa7d" width="300"/>


## How to Use
You can either clone this repository to your SCC home directory or you can directly use it from the ChenLab Z drive path `/net/claustrum/mnt/data/Projects/Homecage/VideoAnalysisSCC_V2`

### Step 1: Setting up your SCC account
Video analysis of the training module view is run using the [Shared Computing Cluster(SCC)](https://www.bu.edu/tech/support/research/computing-resources/scc/). To make sure you have an accessible SCC account, log on to the [SCC dashboard](https://scc-ondemand2.bu.edu/pun/sys/dashboard) using your BU Kerberos email and password. If you were able to log in with no issues, you can move on to the next step. Otherwise, contact Jerry Chen, to add your BU account to the SCC lab project.

### Step 2: Creating an Anaconda environment (ONLY NEED TO DO ONCE)
If this is your first time setting up an Anaconda environment on the SCC, read the SCC-provided instructions on setting up a .condarc file. 
https://www.bu.edu/tech/support/research/software-and-programming/common-languages/python/anaconda/

Once all is done, we can now set up the conda environment used to run this code. 

The conda YML file which contains all the necessary dependencies for this project is in the `conda-environments` folder.
To create an environment with this file, run the following command:

`conda env create -f conda-environments/env.yml`

To be sure the environment was successfully set up, run the command `conda env list`. You should hopefully see **VideoAnalysisENV** in the list of environments.

Once the **VideoAnalysisENV** environment is set up, you don't need to do this again. 


### Step 3: Running analysis
To run the analysis, change the directory to the `scc` folder. The main shell script to analyze is `run_training_module_job_array.sh`. This script takes in two input arguments:

1. Full path to the directory that contains the video files ex. /net/claustrum/test/folder
2. The number ID of the rigs you would like to run analysis on. If you plan to run an analysis on all videos in the directory instead of individual rigs, input `all` as the argument.

Example 1 (*Running video analysis on rigs 6 and 8 with files located in /Projects/Homecage/Videos*):

`qsub run_training_module_job_array.sh /Projects/Homecage/Videos 6 8`

Example 2 (*Running video analysis on all videos with files located in /Projects/Homecage/Videos*):

`qsub run_training_module_job_array.sh /Projects/Homecage/Videos all`

## Dependencies Used:
https://github.com/DeepLabCut/DeepLabCut

https://github.com/matterport/Mask_RCNN

https://github.com/sirfz/tesserocr

https://pjreddie.com/darknet/yolo/
