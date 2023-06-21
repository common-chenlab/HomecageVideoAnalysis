import cv2
import numpy as np
import os
import tensorflow as tf


class CoatClassifier():
	def __init__(self, model_path = None):
		""" Object that loads an image classification model (e.g. classify mouse as either black coat or white coat from training module videos) 
		Parameters
		-----------
		model_path : string
			Full path to exported model (either folder or .h5)
		"""

		# make sure model exists
		if not os.path.isfile(model_path):
			raise ValueError(f'Weights path "{model_path}" does not point to a file.')

		# create cnn used 
		self.model = tf.keras.models.Sequential()
		self.model.add(tf.keras.layers.Conv2D(64, 3, input_shape=(224,224,3)))
		self.model.add(tf.keras.layers.Activation('relu'))
		self.model.add(tf.keras.layers.MaxPooling2D((2,2,)))

		self.model.add(tf.keras.layers.Conv2D(128, 3))
		self.model.add(tf.keras.layers.Activation('relu'))
		self.model.add(tf.keras.layers.MaxPooling2D((2,2,)))

		self.model.add(tf.keras.layers.Conv2D(256, 3))
		self.model.add(tf.keras.layers.Activation('relu'))
		self.model.add(tf.keras.layers.MaxPooling2D((2,2,)))

		self.model.add(tf.keras.layers.Flatten())

		self.model.add(tf.keras.layers.Dense(1024))
		self.model.add(tf.keras.layers.Activation('relu'))

		self.model.add(tf.keras.layers.Dense(512))
		self.model.add(tf.keras.layers.Activation('relu'))

		self.model.add(tf.keras.layers.Dense(2))
		self.model.add(tf.keras.layers.Activation('softmax'))

		# load in weights
		self.model.load_weights(model_path)

		# class labels
		self.labels = ['black', 'white']

		print('Successfully loaded in coat recognition model!\n')


	def run_inference(self, frame):

		# process frame before runnning model inference
		frame = cv2.resize(frame, (224, 224)) # resize to trained frame dimensions

		# check frame dimensions 
		# note: modify depending on latest model used
		if frame.ndim == 1:
			raise ValueError("Expecting frame with 3 channels (RGB) ")

		# normalize pixel values 
		batch = np.array([frame*1./255])
		cnn_prediction = self.model.predict(batch) # run inference
		
		# get predicted label & confidence score of prediction
		prediction = np.argmax(cnn_prediction[0])
		confidence = round(cnn_prediction[0][prediction], 3)

		return self.labels[prediction], confidence
