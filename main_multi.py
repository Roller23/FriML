import os
import pickle
import random
import json
import numpy as np
import music21 as m21
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras.utils import to_categorical
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout, Activation
from tensorflow.keras.callbacks import ModelCheckpoint

import utils_multi as utils

# Fix for Manjaro, CUDA 11 (pacman -S python-tensorflow-cuda)
# Fixes: Could not create cudnn handle: CUDNN_STATUS_INTERNAL_ERROR
from tensorflow.compat.v1 import ConfigProto
from tensorflow.compat.v1 import InteractiveSession

config = ConfigProto()
config.gpu_options.allow_growth = True
session = InteractiveSession(config=config)
# xif. If you don't use Manjaro, comment it or something.

def train_for_track(notes, offsets, durations):
  for off, dur in zip(offsets, durations):
    for i in range(0, len(off), 1):
      dur[i] = off[i] + '|' + str(dur[i])

  pitches = utils.get_unique_pitches(notes)
  note_to_int = dict((note, number) for number, note in enumerate(pitches))

  unique_durations = utils.get_unique_pitches(durations)
  duration_to_int = dict((duration, number) for number, duration in enumerate(unique_durations))

  unique_notes_count = len(note_to_int.keys())
  unique_durations_count = len(duration_to_int.keys())

  sequence_length = 20

  network_input = []
  network_output = []
  dur_network_input = []
  dur_network_output = []

  for song in notes:
    for i in range(0, len(song) - sequence_length, 1):
      sequence_in = song[i : i + sequence_length] # s_l notes starting from i offset
      sequence_out = song[i + sequence_length] # current note + s_l
      # map strings to numbers
      network_input.append([note_to_int[char] for char in sequence_in])
      network_output.append(note_to_int[sequence_out])

  for song in durations:
    for i in range(0, len(song) - sequence_length, 1):
      sequence_in = song[i : i + sequence_length] # s_l notes starting from i offset
      sequence_out = song[i + sequence_length] # current note + s_l
      # map strings to numbers
      dur_network_input.append([duration_to_int[char] for char in sequence_in])
      dur_network_output.append(duration_to_int[sequence_out])

  patterns_count = len(network_input)
  dur_patterns_count = len(dur_network_input)

  # reshape the input into a format compatible with LSTM layers
  network_input = np.reshape(network_input, (patterns_count, sequence_length, 1))
  # normalize input
  network_input = network_input / float(unique_notes_count) # normalize input
  # network_output = to_categorical(network_output) # convert the vector to a binary matrix

  dur_network_input = np.reshape(dur_network_input, (dur_patterns_count, sequence_length, 1))
  dur_network_input = dur_network_input / float(unique_durations_count)
  #dur_network_output = to_categorical(dur_network_output)

  model, callbacks = utils.create_model(
    (network_input.shape[1], network_input.shape[2]),
    unique_notes_count,
    'output/weights.hdf5',
    loss_dest=0.5
  )
  dur_model, dur_callbacks = utils.create_model(
    (dur_network_input.shape[1], dur_network_input.shape[2]),
    unique_durations_count,
    'output/weights_dur.hdf5',
    loss_dest=0.5
  )

  class DataGenerator(tf.keras.utils.Sequence):
    def __init__(self, x_col, y_col, seq, outputs, batch_size=32):
      self.batch_size = batch_size
      self.x_col = x_col
      self.y_col = y_col
      self.seq = seq
      self.outputs = outputs

    def __data_generation(self, index):
      'Generates data containing batch_size samples' # X : (n_samples, *dim, n_channels)
      i = index*self.batch_size
      # Initialization
      X = np.empty((self.batch_size*self.seq)).reshape(self.batch_size,self.seq,1)
      y = np.empty((self.batch_size), dtype=int)
      # Generate data
      X[:] = self.x_col[i : i+self.batch_size]
      y[:] = self.y_col[i : i+self.batch_size]
      return X, keras.utils.to_categorical(y, num_classes=self.outputs)

    def __getitem__(self, index):
      'Generate one batch of data'
      X, y = self.__data_generation(index)
      return X, y

    def __len__(self):
      'Denotes the number of batches per epoch'
      return int(np.floor(len(self.y_col)/self.batch_size))


  my_generator = DataGenerator(x_col=network_input, y_col=network_output, seq=sequence_length, outputs=unique_notes_count, batch_size=64)
  dur_generator = DataGenerator(x_col=dur_network_input, y_col=dur_network_output, seq=sequence_length, outputs=unique_durations_count, batch_size=64)

  # start training
  model.fit(my_generator, epochs=100, callbacks=callbacks, batch_size=64)
  dur_model.fit(dur_generator, epochs=100, callbacks=dur_callbacks, batch_size=64)

  return model, dur_model, network_input, dur_network_input

def load_data(note_name, dur_name):
  # Loading notes data
  with open('model/'+note_name+'.p','rb') as fp:
    int_to_note = pickle.load(fp)
  with open('model/'+dur_name+'.p','rb') as fp:
    int_to_duration = pickle.load(fp)
  model = load_model('model/'+note_name+'.hdf5')
  model_dur = load_model('model/'+dur_name+'.hdf5')
  # pattern = []
  # pattern_dur = []
  # for i in range(0,20):
  #   pattern.append(random.randint(0,max(int_to_note.keys())))
  #   pattern_dur.append(random.randint(0,max(int_to_duration.keys())))
  return int_to_note,model,int_to_duration,model_dur

def generate_song(model, network_input, int_to_note, dur_model, dur_input, int_to_duration, output, length=500):
  # training finished, generate output song
  # convert from ints back to class names
  #pitches = utils.get_unique_pitches(track)
  #int_to_note = dict((number, note) for number, note in enumerate(pitches)) # [key => value] = [int => string]
  #unique_durations = utils.get_unique_pitches(durs)
  #int_to_duration = dict((number, duration) for number, duration in enumerate(unique_durations))
  # print(int_to_note)
  # print(int_to_duration)
  prediction_output, dur_prediction_output = utils.construct_song(model, network_input, int_to_note, dur_model, dur_input, int_to_duration, length=length) # predict notes in the new song
  print('Generated notes\n', prediction_output)
  print('Generated durations\n', dur_prediction_output)
  utils.generate_midi(prediction_output, dur_prediction_output, output) # convert output to a .mid file

def generate_for_server(name, dur_name, key, instrument):
  length = 500
  int_to_note, model = load_data(name)
  int_to_duration, dur_model = load_data(dur_name)
  network_input = []
  dur_network_input = []
  for j in range(0, 20):
    network_input.append(random.randint(0,max(int_to_note.keys())))
    dur_network_input.append(random.randint(0,max(int_to_duration.keys())))

  prediction_output, dur_prediction_output = utils.construct_song(model, network_input, int_to_note, dur_model, dur_network_input, int_to_duration, length=length) # predict notes in the new song
  return utils.generate_json(prediction_output, dur_prediction_output)

def main():
  midis_folder = './midis/VGM/'
  midi_files = map(lambda f: midis_folder + f, os.listdir(midis_folder))
  #midi_files = list(filter(lambda f: 'ashover_simple_chords' in f, midi_files)) # train only on chord files
  print('Converting midis...')
  notes = []
  offsets = []
  durations = []
  i=0
  for file in midi_files:
    if i==5:
      break
    try:
      _notes, _offsets, _durations = utils.convert_midi(file, target_key='G major')
    except:
      os.remove(file)
    
    notes.append(_notes)
    offsets.append(_offsets)
    durations.append(_durations)
    i+=1

  with open('output/notes.json', 'w') as fp:
    json.dump(notes, fp)
  with open('output/offsets.json', 'w') as fp:
    json.dump(offsets, fp)
  for item in durations:
    for i in range(0, len(item), 1):
      item[i] = str(item[i])
  with open('output/durations.json', 'w') as fp:
    json.dump(durations, fp)
  # with open('output/notes.json', 'r') as fp:
  #   notes = json.load(fp)
  # with open('output/offsets.json', 'r') as fp:
  #   offsets = json.load(fp)
  # with open('output/durations.json', 'r') as fp:
  #   durations = json.load(fp)

  print(durations)
  model, dur_model, network_input, dur_network_input = train_for_track(notes, offsets, durations) # TO DO - add support for durations
  print('Done')
  
  pitches = utils.get_unique_pitches(notes)
  int_to_note = dict((number, note) for number, note in enumerate(pitches))
  unique_durations = utils.get_unique_pitches(durations)
  int_to_duration = dict((number, duration) for number, duration in enumerate(unique_durations))
  with open('output/int_to_note.p','wb') as fp:
    pickle.dump(int_to_note,fp,protocol=pickle.HIGHEST_PROTOCOL)
  pattern = []
  for i in range(0,20):
    pattern.append(random.randint(0,max(int_to_note.keys())))
 
  with open('output/int_to_duration.p','wb') as fp:
    pickle.dump(int_to_duration,fp,protocol=pickle.HIGHEST_PROTOCOL)
  pattern_dur = []
  for i in range(0,20):
    pattern_dur.append(random.randint(0, max(int_to_duration.keys())))

  #i = 0
  while True:	
    try:
      #generate_song(model, network_input, notes, dur_model, dur_network_input, durations, 'output'+str(i)+'.mid')
      generate_song(model, pattern, int_to_note, dur_model, pattern_dur, int_to_duration, 'output'+str(i)+'.mid')
    except Exception as e:
      print(e)
    i+=1
    print("Continue?")
    if input()!='y':
      break

if __name__ == '__main__':
 main()