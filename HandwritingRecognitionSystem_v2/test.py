from __future__ import print_function
###
# Copyright 2018 Edgard Chammas. All Rights Reserved.
# Licensed under the Creative Commons Attribution-NonCommercial International Public License, Version 4.0.
# You may obtain a copy of the License at https://creativecommons.org/licenses/by-nc/4.0/legalcode
###

#!/usr/bin/python

import tensorflow as tf
import sys
import os
import cv2
import numpy as np
import codecs
import math

# try:
# 	reload(sys)  # Python 2
# 	sys.setdefaultencoding('utf8')
# except NameError:
# 	pass         # Python 3

from .config import cfg
from .util import LoadClasses
from .util import LoadModel
from .util import ReadData
from .util import LoadList
from .cnn import CNN
from .cnn import WND_HEIGHT
from .cnn import WND_WIDTH
from .cnn import MPoolLayers_H
from .rnn import RNN


# if cfg.WriteDecodedToFile == True:
# 	DecodeLog = codecs.open("decoded.txt", "w", "utf-8")


def run(model_location="HandwritingRecognitionSystem_v2/MATRICULAmodel"):
	cfg.SaveDir = model_location
	list_file = f'{model_location}/list'
	imgs_path = f'{model_location}/Images/'
	labels_path = f'{model_location}/Labels/'

	cfg.CHAR_LIST = f'{model_location}/CHAR_LIST'

	tf.compat.v1.reset_default_graph()

	Classes = LoadClasses(cfg.CHAR_LIST)

	NClasses = len(Classes)

	FilesList = LoadList(cfg.TEST_LIST)

	WND_SHIFT = WND_WIDTH - 2

	VEC_PER_WND = WND_WIDTH / math.pow(2, MPoolLayers_H)

	phase_train = tf.Variable(True, name='phase_train')

	x = tf.compat.v1.placeholder(tf.float32, shape=[None, WND_HEIGHT, WND_WIDTH])

	SeqLens = tf.compat.v1.placeholder(shape=[cfg.BatchSize], dtype=tf.int32)

	x_expanded = tf.expand_dims(x, 3)

	Inputs = CNN(x_expanded, phase_train, 'CNN_1', cfg)

	logits = RNN(Inputs, SeqLens, 'RNN_1', cfg)

	# CTC Beam Search Decoder to decode pred string from the prob map
	decoded, log_prob = tf.nn.ctc_beam_search_decoder(inputs=logits, sequence_length=SeqLens)

	#Reading test data...
	InputListTest, SeqLensTest, _ = ReadData(cfg.TEST_LOCATION, cfg.TEST_LIST, cfg.TEST_NB, WND_HEIGHT, WND_WIDTH, WND_SHIFT, VEC_PER_WND, '')

	print('Initializing...')

	session = tf.compat.v1.Session()

	session.run(tf.compat.v1.global_variables_initializer())

	LoadModel(session, cfg.SaveDir+'/')

	try:
		session.run(tf.compat.v1.assign(phase_train, False))

		randIxs = range(0, len(InputListTest))

		start, end = (0, cfg.BatchSize)

		batch = 0
		while end <= len(InputListTest):
			batchInputs = []
			batchSeqLengths = []
			for batchI, origI in enumerate(randIxs[start:end]):
				batchInputs.extend(InputListTest[origI])
				batchSeqLengths.append(SeqLensTest[origI])

			feed = {x: batchInputs, SeqLens: batchSeqLengths}
			del batchInputs, batchSeqLengths

			Decoded = session.run([decoded], feed_dict=feed)[0]
			del feed

			trans = session.run(tf.sparse.to_dense(Decoded[0]))

			decodedStr = ""

			for j in range(0, len(trans[0])):
				if trans[0][j] == 0:
					if (j != (len(trans[0]) - 1)):
						if trans[0][j+1] == 0: break
						else: decodedStr = "%s%s" % (decodedStr, Classes[trans[0][j]])
					else:
						break
				else:
					if trans[0][j] == (NClasses - 2):
						if (j != 0): decodedStr = "%s " % (decodedStr)
						else: continue
					else:
						decodedStr = "%s%s" % (decodedStr, Classes[trans[0][j]])

			decodedStr = decodedStr.replace("<SPACE>", " ")
			print("|" + decodedStr + "|")
			return decodedStr

	except (KeyboardInterrupt, SystemExit, Exception) as e:
		print("[Error/Interruption] %s" % str(e))
		print("Clossing TF Session...")
		session.close()
		print("Terminating Program...")
		sys.exit(0)


if __name__ == "__main__":
	run()
