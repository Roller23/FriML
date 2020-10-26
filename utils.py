import numpy as np
import music21 as m21
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras.utils import to_categorical
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout, Activation
from tensorflow.keras.callbacks import ModelCheckpoint

def create_model(shape, density, filename="./output/weights.hdf5", loss_dest=0.0001):
  print('shape', shape)
  model = Sequential()
  model.add(LSTM(
    256,
    input_shape=shape,
    return_sequences=True
  ))
  model.add(Dropout(0.3))
  model.add(LSTM(512, return_sequences=True))
  model.add(Dropout(0.3))
  model.add(LSTM(256))
  model.add(Dense(256))
  model.add(Dropout(0.3))
  model.add(Dense(density))
  model.add(Activation('softmax'))
  model.compile(loss='categorical_crossentropy', optimizer='rmsprop')
  callbacks_list = [ModelCheckpoint(
    filename,
    monitor='loss',
    save_freq='epoch', # save after every epoch
    verbose=0,
    save_best_only=True, # save only if the model is better than in the previous iteration
    mode='min' # set to min because loss is being monitored
  )]
  class haltCallback(tf.keras.callbacks.Callback):
    def on_epoch_end(self, epoch, logs={}):
      if (logs.get('loss') <= loss_dest): # stop at certain loss
        print("\nReached predefined loss, training finished early\n")
        self.model.stop_training = True
  trainingStopCallback = haltCallback()
  callbacks_list.append(trainingStopCallback)
  return (model, callbacks_list)

def construct_song(model, network_input, int_lut, length=200):
  pattern = network_input[np.random.randint(0, len(network_input) - 1)] # pick a random sequence to start
  output = []
  for note_index in range(length):
    # reshape and normalize
    prediction_input = np.reshape(pattern, (1, len(pattern), 1)) / float(len(int_lut.keys()))
    prediction = model.predict(prediction_input, verbose=0)
    # index = np.argmax(prediction) # generates repetitiveness
    choice = np.random.choice(prediction[0], 1, p=prediction[0], replace=False)[0]
    index = np.where(prediction[0] == choice)[0][0] # workaround?
    result = int_lut[index]
    output.append(result)
    # pattern.append(index) # doesnt work
    pattern = np.append(pattern, index) # workaround
    pattern = pattern[1 : len(pattern)]
  return output

def generate_midi(notes, output='output.mid'):
  offset = 0
  output_notes = []
  for chord in notes:
    if '.' in chord: # it's a chord
      notes = []
      for current_note in chord.split('.'):
        new_note = m21.note.Note(current_note)
        new_note.storedInstrument = m21.instrument.Piano()
        notes.append(new_note)
      new_chord = m21.chord.Chord(notes)
      new_chord.offset = offset
      output_notes.append(new_chord)
    else: # it's a single note
      new_note = m21.note.Note(chord)
      new_note.offset = offset
      new_note.storedInstrument = m21.instrument.Piano()
      output_notes.append(new_note)
    offset += 0.5

  midi_stream = m21.stream.Stream(output_notes)
  midi_stream.write('midi', fp=output)

def convert_midi(path, target_key=None):
  stream = m21.converter.parse(path)
  parts = m21.instrument.partitionByInstrument(stream)
  key = stream.analyze('key')
  key_str = str(key)
  print('Key detected ' + key_str)
  if target_key != None and key_str != target_key:
    print('Transposing to ' + target_key)
    interval = m21.interval.Interval(key.tonic, m21.pitch.Pitch('G'))
    stream = stream.transpose(interval)
    parts = m21.instrument.partitionByInstrument(stream)
  track = None
  if parts:
    track = parts.parts[0] if len(parts.parts[0].pitches) > 0 else parts.parts[1]
  else:
    track = stream.flat.notes
  notes = []
  durations = []
  for event in track:
    if isinstance(event, m21.note.Note):
      notes.append(str(event.pitch))
      durations.append(event.duration.quarterLength)
    elif isinstance(event, m21.chord.Chord):
      notes.append('.'.join(str(n) for n in event.pitches))
      durations.append(event.duration.quarterLength)
  print('Converted ' + path)
  return notes, durations

def get_unique_pitches(track):
  s = set()
  for song in track:
    s.update(set(song))
  return sorted(s)