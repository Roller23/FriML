import os
import numpy as np
import music21 as m21
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras.utils import to_categorical
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout, Activation
from tensorflow.keras.callbacks import ModelCheckpoint

if __name__ == '__main__':

  import utils

  midis_folder = './midis/Nottingham/train/'
  midi_files = map(lambda f: midis_folder + f, os.listdir(midis_folder))
  midi_files = list(filter(lambda f: 'ashover_simple_chords' in f, midi_files)) # train only on chord files
  print('Converting midis...')
  track = []
  for file in midi_files:
    track = track + utils.convert_midi(file)
  
  # track = utils.convert_midi('./midis/VGM/green.mid') # a single track

  print('Done')

  def train_for_song(notes):
    pitches = sorted(set(notes))
    note_to_int = dict((note, number) for number, note in enumerate(pitches))

    unique_notes_count = len(note_to_int.keys())

    sequence_length = 30

    network_input = []
    network_output = []

    for i in range(0, len(notes) - sequence_length, 1):
      sequence_in = notes[i : i + sequence_length] # s_l notes starting from i offset
      sequence_out = notes[i + sequence_length] # current note + s_l
      # map strings to numbers
      network_input.append([note_to_int[char] for char in sequence_in])
      network_output.append(note_to_int[sequence_out])

    patterns_count = len(network_input)

    # reshape the input into a format compatible with LSTM layers
    network_input = np.reshape(network_input, (patterns_count, sequence_length, 1))
    # normalize input
    network_input = network_input / float(unique_notes_count) # normalize input
    network_output = to_categorical(network_output) # convert the vector to a binary matrix

    model, callbacks = utils.create_model(
      (network_input.shape[1], network_input.shape[2]),
      unique_notes_count,
      loss_dest=0.5
    )

    # start training
    model.fit(network_input, network_output, epochs=50, callbacks=callbacks, batch_size=64)

    # training finished, generate output song
    # convert from ints back to class names
    int_to_note = dict((number, note) for number, note in enumerate(pitches)) # [key => value] = [int => string]
    prediction_output = utils.construct_song(model, network_input, int_to_note, length=500) # predict notes in the new song
    print('Generated notes\n', prediction_output)
    utils.generate_midi(prediction_output) # convert output to a .mid file

  train_for_song(track)