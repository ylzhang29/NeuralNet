from numpy import loadtxt
from keras.layers import Input, Dense
from keras.models import Model, Sequential
from keras.optimizers import SGD
from keras.regularizers import l1
from keras.regularizers import l2
from keras import layers
from keras.callbacks import ModelCheckpoint
from keras.callbacks import TensorBoard
import numpy as np
import os as os
import configparser as cp
import time as time

# split into input (X) and output (y) variables

class NetworkBuilder:

	def loadData(self):		
		dataset = loadtxt(self.DATA, delimiter=",")
		X = dataset[:,self.X_COLUMNS]
		y = dataset[:,self.Y_COLUMNS]
		def min_max(x):
			return [np.round((xx-np.min(x))/(1.0*(np.max(x)-np.min(x))),2) for xx in x]
		for i in range(X.shape[1]):
			X[:,i] = min_max(X[:,i])
		for i in range(y.shape[1]):
			y[:,i] = min_max(y[:,i])
		return X, y

	def generateMLP(self):
		layer_0 = Input(shape=(len(self.X_COLUMNS),))
		ltype = self.REGTYPE
		if self.REGTYPE == "none":
			ACREG=""
		if self.REGTYPE != "none":	
			ACREG = "activity_regularizer="+ltype+"("+self.REGVAL+")"
		for i in range(self.NUM_HIDDEN_LAYERS):
			i = i*2
			i = i+1
			layer_i="layer_"+str(i)+" = Dense("+str(self.HL_UNITS)+", activation='relu',"+ACREG+",)(layer_"+(str(i-1))+")\nlayer_"+str(i+1)+" = layers.Dropout("+self.DROPVAL+")(layer_"+(str(i))+")"
			exec(layer_i)	
		layer_out = []
		layer_out.clear()
		for i in range(len(self.LOSS)):
			if self.LOSS[i]=='mean_squared_error':
				actif = 'linear'
			if self.LOSS[i]=='categorical_crossentropy':
				actif = 'softmax'
			if self.LOSS[i]=='mean_squared_logarithmic_error':
				actif = 'linear'
			if self.LOSS[i]=='mean_absolute_error':
				actif = 'linear'
			if self.LOSS[i]=='mean_squared_logarithmic_error':
				actif = 'linear'
			if self.LOSS[i]=='binary_crossentropy':
				actif = 'sigmoid'
			if self.LOSS[i]=='hinge':
				actif = 'tanh'
			if self.LOSS[i]=='squared_hinge':
				actif = 'tanh'
			if self.LOSS[i]=='sparse_categorical_crossentropy':
				actif = 'softmax'
			if self.LOSS[i]=='kullback_libler_divergence':
				actif = 'softmax'							
			layer_out_i="layer_out_"+str(i)+" = Dense(1, activation='"+actif+"')(layer_"+str(self.NUM_HIDDEN_LAYERS*2)+")"
			exec(layer_out_i)
			layer_out.append("layer_out_"+str(i)+"")
		outputs = ",".join(layer_out)
		model = eval("Model(inputs=layer_0, outputs=["+outputs+"])")
		# compile the keras model
		opt = SGD(lr=self.LR, momentum=self.MOMENTUM, decay=self.DECAY)
		model.compile(loss=self.LOSS, optimizer=opt, metrics=self.METRICS)
		print(model.summary())
		return(model)

	def loadWeights(self,model,fileName):
		model.load_weights(fileName)
		return(model)

	def fitModel(self,X,y,model):
		os.system("rm -r my_log_dir")
		os.mkdir("my_log_dir")
		tensorboard = TensorBoard(log_dir="my_log_dir")
		checkpoint = ModelCheckpoint(self.ID+".hdf5", verbose=1, save_best_only=False, mode='max')
		callbacks_list = [checkpoint,tensorboard]
		history = model.fit(X, y, epochs=self.EPOCHS, batch_size=self.BATCH_SIZE,callbacks=callbacks_list)
		print("enter in terminal to use TensorBoard 2.0.2 at http://localhost:6008/ : 'tensorboard --logdir=my_log_dir'")
		return(model)

	def makePredictions(self,model,X):
		yhat = model.predict(X)
		return(yhat)    

	def __init__(self):

		def ConfigSectionMap(section):
			dict1 = {}
			options = Config.options(section)
			for option in options:
			    try:
			        dict1[option] = Config.get(section, option)
			        if dict1[option] == -1:
			            DebugPrint("skip: %s" % option)
			    except:
			        print("exception on %s!" % option)
			        dict1[option] = None
			return dict1	
		self.ROOT_PATH = '/Volumes/HD/Code/python/2019/DeepAdvisors/NeuralNet/'
		Config = cp.ConfigParser()
		Config.read(self.ROOT_PATH+"config.ini")
		sections = Config.sections()[0]
		self.X_COLUMNS = list(ConfigSectionMap(sections)['x_columns'].split(','))
		for i in range(len(self.X_COLUMNS)):
			self.X_COLUMNS[i] = int(self.X_COLUMNS[i])
		self.Y_COLUMNS = list(ConfigSectionMap(sections)['y_columns'].split(','))
		for i in range(len(self.Y_COLUMNS)):
			self.Y_COLUMNS[i] = int(self.Y_COLUMNS[i])
		self.LOSS = ConfigSectionMap("NetworkParameters")['loss'].split(',')
		self.METRICS = ConfigSectionMap("NetworkParameters")['metrics'].split(',')
		self.NUM_HIDDEN_LAYERS = int(ConfigSectionMap("NetworkParameters")['num_hidden_layers'])
		self.HL_UNITS = int(ConfigSectionMap("NetworkParameters")['hl_units'])
		self.EPOCHS = int(ConfigSectionMap("NetworkParameters")['epochs'])
		self.BATCH_SIZE = int(ConfigSectionMap("NetworkParameters")['batch_size'])
		self.DATA = ConfigSectionMap("NetworkParameters")['data']
		self.LR = float(ConfigSectionMap("NetworkParameters")['lr'])
		self.MOMENTUM = float(ConfigSectionMap("NetworkParameters")['momentum'])
		self.DECAY = float(ConfigSectionMap("NetworkParameters")['decay'])
		self.REGTYPE = ConfigSectionMap("NetworkParameters")['regularization_type']
		self.REGVAL = ConfigSectionMap("NetworkParameters")['regularization_val']
		self.ID = ConfigSectionMap("NetworkParameters")['unique_model_id']
		self.DROPVAL = ConfigSectionMap("NetworkParameters")['dropout_val']
