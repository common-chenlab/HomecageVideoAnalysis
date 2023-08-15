import datetime
import sys
import stat
import shutil
import os
import traceback
import time
from chenlabpylib import chenlab_filepaths
from paths import folder_paths, sensitive_information_folder

sys.path.append(chenlab_filepaths(path = sensitive_information_folder))
from sensitive_info import BLUE_IRIS_COMPUTER_IP


""" utility functions for video analysis """

def ospath(path):
    """ create_modified version of chenlab_filepaths from chenlabpylib. Some video paths might contain IP addresses which cannot be public to repo"""
    
    # create hash table of letter network drives and SCC mounted paths
    if BLUE_IRIS_COMPUTER_IP in path:
        if '/net/{}/video-data'.format(BLUE_IRIS_COMPUTER_IP) in path:
            path = path.replace('/net/{}/video-data'.format(BLUE_IRIS_COMPUTER_IP), 'N:\\BlueIris')
        elif 'N:\\BlueIris' in path:
            path = path.replace('N:\\BlueIris', '/net/{}/video-data'.format(BLUE_IRIS_COMPUTER_IP))
        else:
            return path
             
        # running on linux
        if sys.platform == 'linux':	
            path = path.replace('\\', '/')
        else: # running on Windows
            path = path.replace('/', '\\')
             
        return path
        
    else: # use general chenlab_filepaths
        return chenlab_filepaths(path=path)
    


def move_videos_2_scc_scratch(video_path_list):
    """ copy video paths to SCC compute node's local scratch folder (avoid heavy IO(ffmpeg) on Blue Iris computer)
    will copy all video files in list to this location. SCC will automatically delete these files after 30 days or you can manually delete. """

    scc_node_name = os.environ["HOSTNAME"].split(".")[0]
    scc_username = os.environ["LOGNAME"]
    scratch_dir = "/net/{}/scratch/{}/videoanalysis".format(scc_node_name, scc_username)
    os.makedirs(scratch_dir, exist_ok = True)

    # copy files from network drive to computer node scratch folder
    temp_video_path_list = video_path_list
    video_path_list = []
    for video_path in temp_video_path_list:
        shutil.copy(video_path, scratch_dir)
        video_path_list.append(os.path.join(scratch_dir, os.path.basename(video_path)))
    
    time.sleep(3) # add wait time of 3 seconds

    return video_path_list



def create_logfile(log_file_path):
	""" create a log file with SCC job/local information 
	as well details of the exception caught """

	# code on scc
	if sys.platform == 'linux':
		# scc job information
		if "SGE_TASK_ID" in os.environ:
			task_id = os.environ["SGE_TASK_ID"]
		else:
			task_id = int(0)
		job_id = str(os.environ["JOB_ID"])
		job_name = str(os.environ["JOB_NAME"])

	# code in windows
	else:
		# code on local windows
		task_id = int(0)
		job_id = str(0)
		job_name = 'WINDOWSRUN'

	job_information = ('JOB NAME: ' + str(job_name) + '\n'
					+ 'JOB ID: ' + str(job_id) + '\n'
					+ 'TASK ID: ' + str(task_id) + '\n')
	exception_caught = '\nEXCEPTION CAUGHT: ' + traceback.format_exc() + '\n'

	# create log file of exception caught / open log file
	with open(log_file_path, 'w') as fp:
		# write to file
		fp.write(job_information)
		fp.write(exception_caught)

	# modify permissions for log file
	os.chmod(log_file_path, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)


def create_mat_subfolder(videofilename, training_module_id, camera_view, videodatetime, cageID = ""):
	""" create path to mat subfolder to save .MAT files"""

	if camera_view == 'CV':
		mat_folder_path = chenlab_filepaths(path = folder_paths['matfilecv'])
	elif camera_view == 'TM':
		mat_folder_path = chenlab_filepaths(path = folder_paths['matfiletm'])
	else:
		raise ValueError("camera_view is neither TM or CV.")

	# create rig short name
	rig_name = camera_view + "_" + str(training_module_id)

	# convert date object to string
	videodate_str = videodatetime.date().strftime("%Y%m%d")

	# create mat subfolder path
	mat_subfolder_path = mat_folder_path

	for folder in [rig_name, str(cageID), videodate_str, videofilename]:
		mat_subfolder_path = os.path.join(mat_subfolder_path, folder)

		# create and edit file permissions
		mkdir2(path = mat_subfolder_path)

	return mat_subfolder_path


def format_filename(cameraname, datetime_obj, filextension = 'mat'):
	""" use the camera name and datetimte object to create MAT file name with preferred format """

	formatted_cameraname = format_cameraname(cameraname = cameraname)
	formatted_timestamp = format_timestamp(datetime_obj = datetime_obj)

	# combine all formatted changes
	formatted_filename = "{}_{}.{}".format(formatted_cameraname, formatted_timestamp, filextension)

	return formatted_filename


def format_cameraname(cameraname):
	"""	convert camera name to digit format TM = 0, CV1 = 1, CV2 = 2, CV3 = 3 """

	cameraview_conversion = {'TM': "0", 'CV1': "1", 'CV2': "2", 'CV3': "3"}
	cameraview, rig_no = cameraname.split('_')
	rig_no = "{:02d}".format(int(rig_no))

	formatted_cameraname = "{}{}".format(rig_no, cameraview_conversion[cameraview])

	return formatted_cameraname


def format_timestamp(datetime_obj):
	""" convert datetime to digit format YYYYMMDDHHMMSS(MS)(MS)(MS) """

	# check if input is in string format, then convert to datetime obj
	if isinstance(datetime_obj, str):
		datetime_obj = datetime.datetime.strptime(datetime_obj, '%m/%d/%Y, %H:%M:%S')

	year, month, day = datetime_obj.year, datetime_obj.month, datetime_obj.day
	hour, minute, second = datetime_obj.hour, datetime_obj.minute, datetime_obj.second
	millisecond = 0 # using milliseconds at 0 for now. No millisecond precision

	formatted_timestamp = "{:04d}{:02d}{:02d}{:02d}{:02d}{:02d}{:03d}".format(year, month, day, 
		hour, minute, second, millisecond)

	return formatted_timestamp


def get_timestamp_offset(init, curr):
	""" get offset between current datetime(current_timestamp) and initial datetime(init_timestamp)  """

	# get datetime difference
	diff = curr - init

	# get difference in seconds
	diff_in_secs = diff.total_seconds()

	return diff_in_secs


def parse_filename(filename):
	""" parse video filename 
	note: assuming BlueIris videos have filename structure such as: TM_6.20220310_190000.mp4 """

	camera_name, file_datetime, *ext = filename.split('.')

	# get cameraview, and rig_no (+ other such as cage IDs)
	camera_view, rig_no, *other = camera_name.split('_')

	# if cage ID in camera_name
	if other:
		cageIDs = other[0]

		# double-check cageIDs match either "12" or "23"
		if cageIDs not in ["12", "23"]:
			raise ValueError("Cage IDs do not match either 12 or 23")

		cageIDs = [int(char) for char in cageIDs]
	else:
		# return -1 if file is training module video
		cageIDs = None

	# get datetime of file name
	file_date, file_time, *extra = file_datetime.split('_')
	year, month, day = file_date[0:4], file_date[4:6], file_date[6:]
	hour, minute, sec = file_time[0:2], file_time[2:4], file_time[4:]
	datetime_object = datetime.datetime(year = int(year), day = int(day), month = int(month),
		hour = int(hour), minute = int(minute), second = int(sec))

	# return python dictionary with rig number, camera view, and datetime object
	return {'rig_no': int(rig_no), 'camera_view': str(camera_view), 'datetime': datetime_object, 'cageIDs': cageIDs}


def mkdir2(path):
	""" create directory (custom version) """
	if not os.path.exists(path): 
		os.makedirs(path, exist_ok = True)
		os.chmod(path, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)
		print("Created ", path)
	else:
		print(path, "already exists")


def resize_cropped_frame(position, max_width, max_height, aspect_ratio):
	""" add padding form frame to maintain a global 'aspect_ratio' where aspect ratio = width/height"""
	
	x, y, w, h = position
	x, y, w, h = int(x*max_width), int(y*max_height), int(w*max_width), int(h*max_height)
	new_height = int(round(w/aspect_ratio))
	
	# if new_height given preferred aspect ratio is greater than original height
	if new_height >= h and (y+new_height) < max_height:
		add_padding_h = new_height - h
		h = new_height
		add_padding = ['y', add_padding_h]
	else:
		new_width = int(round(aspect_ratio * h))
		add_padding_w = new_width - w
		w = new_width
		add_padding = ['x', add_padding_w]
	return add_padding


def expand_dimension(origin, current_size, new_size, max_size, axis = ''):

	new_size_diff = new_size - current_size
	add_to_sides = new_size_diff // 2
	remainder_diff = new_size_diff % 2

	# if addition to sides exceed frame boundry
	side0_rem = max(0, add_to_sides - origin)
	side1_rem = max(0, ((origin+current_size) + add_to_sides) - max_size)

	# add to current coordinates
	new_origin = max(0, origin - add_to_sides) - side1_rem
	new_origin_2 = min(max_size, (origin + current_size) + add_to_sides) + side0_rem

	if (new_origin - remainder_diff) >= 0:
		new_origin -= remainder_diff
	elif (new_origin_2 + remainder_diff) <= max_size:
		new_origin_2 += remainder_diff
	else:
		raise ValueError("Issue with going out of bounds in frame for {}-axis in resize_cropped_frame function".format(axis))

	# change to new values
	return new_origin, (new_origin_2 - new_origin)
