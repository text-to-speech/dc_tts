# -*- coding: utf-8 -*-
# /usr/bin/python2
'''
By kyubyong park. kbpark.linguist@gmail.com.
https://www.github.com/kyubyong/dc_tts
'''

from __future__ import print_function

import os
from time import time

from hyperparams import Hyperparams as hp
import numpy as np
import tensorflow as tf
from train import Graph
from utils import *
from data_load import load_data
from scipy.io.wavfile import write
from tqdm import tqdm

def synthesize():
    # Load data
    L, texts_len = load_data("synthesize")

    # Load graph
    g = Graph(mode="synthesize"); print("Graph loaded")

    with tf.Session() as sess:
        sess.run(tf.global_variables_initializer())

        # Restore parameters
        var_list = tf.get_collection(tf.GraphKeys.TRAINABLE_VARIABLES, 'Text2Mel')
        saver1 = tf.train.Saver(var_list=var_list)
        saver1.restore(sess, tf.train.latest_checkpoint(hp.logdir + "1"))
        print("Text2Mel Restored!")

        var_list = tf.get_collection(tf.GraphKeys.TRAINABLE_VARIABLES, 'SSRN') + \
                   tf.get_collection(tf.GraphKeys.GLOBAL_VARIABLES, 'gs')
        saver2 = tf.train.Saver(var_list=var_list)
        saver2.restore(sess, tf.train.latest_checkpoint(hp.logdir + "2"))
        print("SSRN Restored!")

        # Feed Forward
        ## mel
        Y = np.zeros((len(L), hp.max_T, hp.n_mels), np.float32)
        prev_max_attentions = np.zeros((len(L),), np.int32)
        start = time()
        for j in tqdm(range(hp.max_T)):
            _gs, _Y, _max_attentions, _alignments = \
                sess.run([g.global_step, g.Y, g.max_attentions, g.alignments],
                         {g.L: L,
                          g.mels: Y,
                          g.prev_max_attentions: prev_max_attentions})
            Y[:, j, :] = _Y[:, j, :]
            prev_max_attentions = _max_attentions[:, j]
        M_sec = time() - start

        # Get magnitude
        Z = sess.run(g.Z, {g.Y: Y})

        # Generate wav files
        if not os.path.exists(hp.sampledir): os.makedirs(hp.sampledir)
        N_sec = 0
        for i, mag in enumerate(Z):
            print("Working on file", i+1)
            os.makedirs(hp.sampledir+"mags", exist_ok=True)
            np.save(hp.sampledir + "mags/{}.npy".format(i+1), mag)
            
            start = time()
            wav = spectrogram2wav(mag)
            N_sec += time() - start
            
            write(hp.sampledir + "/{}.wav".format(i+1), hp.sr, wav)
            
        print ("{} text_to_mel seconds".format(M_sec), "{} mel_to_wav seconds".format(N_sec), "{} characters".format(texts_len))

if __name__ == '__main__':
    synthesize()
    print("Done")


