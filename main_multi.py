import os
import numpy as np
import music21 as m21
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras.utils import to_categorical
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout, Activation
from tensorflow.keras.callbacks import ModelCheckpoint

import utils_multi as utils

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
  network_output = to_categorical(network_output) # convert the vector to a binary matrix

  dur_network_input = np.reshape(dur_network_input, (dur_patterns_count, sequence_length, 1))
  dur_network_input = dur_network_input / float(unique_durations_count)
  dur_network_output = to_categorical(dur_network_output)

  model, callbacks = utils.create_model(
    (network_input.shape[1], network_input.shape[2]),
    unique_notes_count,
    loss_dest=0.5
  )
  dur_model, dur_callbacks = utils.create_model(
    (dur_network_input.shape[1], dur_network_input.shape[2]),
    unique_durations_count,
    loss_dest=0.5
  )

  # start training
  model.fit(network_input, network_output, epochs=10, callbacks=callbacks, batch_size=64)
  dur_model.fit(dur_network_input, dur_network_output, epochs=10, callbacks=dur_callbacks, batch_size=64)

  return model, dur_model, network_input, dur_network_input

def generate_song(model, network_input, track, dur_model, dur_input, durs, output, length=500):
  # training finished, generate output song
  # convert from ints back to class names
  pitches = utils.get_unique_pitches(track)
  int_to_note = dict((number, note) for number, note in enumerate(pitches)) # [key => value] = [int => string]
  unique_durations = utils.get_unique_pitches(durs)
  int_to_duration = dict((number, duration) for number, duration in enumerate(unique_durations))
  # print(int_to_note)
  # print(int_to_duration)
  prediction_output, dur_prediction_output = utils.construct_song(model, network_input, int_to_note, dur_model, dur_input, int_to_duration, length=length) # predict notes in the new song
  print('Generated notes\n', prediction_output)
  print('Generated durations\n', dur_prediction_output)
  utils.generate_midi(prediction_output, dur_prediction_output, output) # convert output to a .mid file

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

  print(durations)
  model, dur_model, network_input, dur_network_input = train_for_track(notes, offsets, durations) # TO DO - add support for durations
  print('Done')
  
  i = 0
  while True:	
    try:
      generate_song(model, network_input, notes, dur_model, dur_network_input, durations, 'output'+str(i)+'.mid')
    except Exception as e:
      print(e)
    i+=1
    print("Continue?")
    if input()!='y':
      break

if __name__ == '__main__':
 main()