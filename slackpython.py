import requests
import json
import sys

import utils
from paths import sensitive_information_folder
sys.path.append(utils.ospath(path = sensitive_information_folder))
from sensitive_info import SLACK_CHENLAB_URL

""" Send SLACK notifications to specific channels on python """
# Date Created: 01/04/2022

# SLACK workspace URL ChenLab
url = SLACK_CHENLAB_URL


def SendSlackNotification(message = None, channel = None):
	"""
	message: string
	Message to send to slack

	channel: (optional) string
	direct message to specific channel
	"""

	# payload dictionary
	payload = {"text": "", "channel": ""}

	if message:
		payload["text"] = message

	if channel:
		payload["channel"] = channel

	# create json 
	myobj = json.dumps(payload)

	# post request to slack
	x = requests.post(url, data = myobj)