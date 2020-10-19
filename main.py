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

songs = [convert_midi('./midis/VGM/tears.mid') + convert_midi('./midis/VGM/green.mid') + convert_midi('./midis/VGM/dirth.mid')]

def train_for_song(notes):
  pitches = sorted(set(notes))
  note_to_int = dict((note, number) for number, note in enumerate(pitches))

  unique_notes_count = len(note_to_int.keys())

  print('Song length ' + str(len(notes)))
  sequence_length = 3

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

  model = Sequential()
  model.add(LSTM(
    256,
    input_shape=(network_input.shape[1], network_input.shape[2]),
    return_sequences=True
  ))
  model.add(Dropout(0.3))
  model.add(LSTM(512, return_sequences=True))
  model.add(Dropout(0.3))
  model.add(LSTM(256))
  model.add(Dense(256))
  model.add(Dropout(0.3))
  model.add(Dense(unique_notes_count))
  model.add(Activation('softmax'))
  model.compile(loss='categorical_crossentropy', optimizer='rmsprop')

  filepath = "./output/weights.hdf5"
  callbacks_list = [ModelCheckpoint(
    filepath,
    monitor='loss',
    save_freq='epoch', # save after every epoch
    verbose=0,
    save_best_only=True, # save only if the model is better than in the previous iteration
    mode='min' # set to min because loss is being monitored
  )]

  # start training
  model.fit(network_input, network_output, epochs=100, callbacks=callbacks_list)

  # training finished, generate output song

  int_to_note = dict((number, note) for number, note in enumerate(pitches))

  pattern = network_input[np.random.randint(0, len(network_input) - 1)] # pick a random note to start
  prediction_output = []

  for note_index in range(500):
    # reshape and normalize
    prediction_input = np.reshape(pattern, (1, len(pattern), 1)) / float(unique_notes_count)
    prediction = model.predict(prediction_input, verbose=0)
    index = np.argmax(prediction)
    result = int_to_note[index]
    prediction_output.append(result)
    # pattern.append(index) # doesnt work
    pattern = np.append(pattern, index)
    pattern = pattern[1 : len(pattern)]

  offset = 0
  output_notes = []
  print(prediction_output)
  for pattern in prediction_output:
    if '.' in pattern: # pattern is a chord
      notes = []
      for current_note in pattern.split('.'):
        new_note = m21.note.Note(current_note)
        new_note.storedInstrument = m21.instrument.Piano()
        notes.append(new_note)
      new_chord = m21.chord.Chord(notes)
      new_chord.offset = offset
      output_notes.append(new_chord)
    else: # pattern is a note
      new_note = m21.note.Note(pattern)
      new_note.offset = offset
      new_note.storedInstrument = m21.instrument.Piano()
      output_notes.append(new_note)
    offset += 0.5

  midi_stream = m21.stream.Stream(output_notes)
  midi_stream.write('midi', fp='output.mid')

train_for_song(songs[0])