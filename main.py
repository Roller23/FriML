import os
import numpy as np
import multiprocessing as mp
import music21 as m21
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras.utils import to_categorical
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout, Activation
from tensorflow.keras.callbacks import ModelCheckpoint

import utils

def convert_midi(path):
  midi = m21.converter.parse(path)
  parts = m21.instrument.partitionByInstrument(midi)
  track = None
  if parts:
    track = parts.parts[0] if len(parts.parts[0].pitches) > 0 else parts.parts[1]
  else:
    track = midi.flat.notes
  notes = []
  for event in track:
    if isinstance(event, m21.note.Note):
      notes.append(str(event.pitch))
    elif isinstance(event, m21.chord.Chord):
      notes.append('.'.join(str(n) for n in event.pitches))
  print('Converted ' + path)
  return notes

pool = mp.Pool(mp.cpu_count())

# midis_folder = './midis/VGM/'
# midi_files = map(lambda f: midis_folder + f, os.listdir(midis_folder))
# print('Converting midis...')
# songs = pool.map(convert_midi, midi_files)
# print('Done')

songs = [convert_midi('./midis/VGM/tears.mid')]

def train_for_song(notes):
  pitches = sorted(set(notes))
  note_to_int = dict((note, number) for number, note in enumerate(pitches))

  unique_notes_count = len(note_to_int.keys())

  print('Song length ' + str(len(notes)))
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
    unique_notes_count
  )

  # start training
  model.fit(network_input, network_output, epochs=100, callbacks=callbacks, batch_size=64)

  # training finished, generate output song
  int_to_note = dict((number, note) for number, note in enumerate(pitches))
  prediction_output = utils.construct_song(model, network_input, int_to_note) # predict notes in the new song
  print(prediction_output)
  utils.generate_midi(prediction_output) # convert output to a .mid file

train_for_song(songs[0])