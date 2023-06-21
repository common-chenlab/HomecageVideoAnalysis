# Homecage Video Analysis
<img src="https://github.com/kevry/HomecageVideoAnalysis/assets/45439265/a96640ca-1950-4cc6-a994-8ebe4b33098f" width="200"/>

<img src="https://github.com/kevry/HomecageVideoAnalysis/assets/45439265/6ae90a59-64e3-4569-82ff-8254ad641b48" width="350"/>

## How to Use

### Step 1: Setting up your SCC account
Video analysis of the training module view is run using the [Shared Computing Cluster(SCC)](https://www.bu.edu/tech/support/research/computing-resources/scc/). To make sure you have an accessible SCC account, logon to the [SCC dashboard](https://scc-ondemand2.bu.edu/pun/sys/dashboard) using your BU Kerberos email and password. If you were able to log in with no issues, you can move on to the next step. Otherwise, contact Jerry Chen, to add your BU account to the SCC lab project.

### Step 2: Creating an Anaconda environment (ONLY NEED TO DO ONCE)
If this is your first time setting up an Anaconda environment on the SCC, read the SCC provided instructions on setting up a .condarc file. 
https://www.bu.edu/tech/support/research/software-and-programming/common-languages/python/anaconda/

Once all is set, load up the Anaconda module on the SCC using the following:

`module load miniconda`


### Step 3: Running analysis
To run analysis, change directory to the `scc` folder. The main shell script to analysis is `run_training_module_job_array.sh`. This script will load in all video files from a path you provide, filtering out videos that do not belong in the list of rig numbers you input. An example of running the shell script is below.

`qsub run_training_module_job_array.sh /Projects/Homecage/Videos 6 8 9 10 11`

In this example, we will run video analysis on videos that belong to rig 6,8,9,10,and 11 from the /Projects/Homecage/Videos directory.


## Dependencies Used:
https://github.com/DeepLabCut/DeepLabCut

https://github.com/matterport/Mask_RCNN

https://github.com/sirfz/tesserocr

https://pjreddie.com/darknet/yolo/
