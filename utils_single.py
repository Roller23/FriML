import json
import numpy as np
import music21 as m21
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras.utils import to_categorical
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout, Activation
from tensorflow.keras.callbacks import ModelCheckpoint
from pathlib import Path

majors = dict([("A-", 4),("G#", 4),("A", 3),("A#", 2),("B-", 2),("B", 1),("C", 0),("C#", -1),("D-", -1),("D", -2),("D#", -3),("E-", -3),("E", -4),("F", -5),("F#", 6),("G-", 6),("G", 5)])
minors = dict([("G#", 1), ("A-", 1),("A", 0),("A#", -1),("B-", -1),("B", -2),("C", -3),("C#", -4),("D-", -4),("D", -5),("D#", 6),("E-", 6),("E", 5),("F", 4),("F#", 3),("G-", 3),("G", 2)])

def create_model(shape, density, filename="./output/weights.hdf5", loss_dest=0.0001):
  print('shape', shape)
  Path(filename).parent.mkdir(parents=True, exist_ok=True) # create needed directories if they don't exist
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
  callbacks_list.append(haltCallback())
  return (model, callbacks_list)

def construct_song(model, pattern, int_lut, length=200):
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

def generate_midi(notes, key='C', instrument='piano', output='output.mid'):
  offset = 0
  output_notes = []
  i = m21.instrument.Piano
  if instrument == 'guitar':
    i = m21.instrument.Guitar
  if instrument == 'violin':
    i = m21.instrument.Violin
  if instrument == 'synth':
    i = m21.instrument.ElectricBass
  for chord in notes:
    vars = chord.split('|')
    dur = 0.0
    off = 0.0
    if '/' in vars[1]:
      sp = vars[1].split('/')
      off = float(sp[0]) / float(sp[1])
    else:
      off = float(vars[1])
    if '/' in vars[2]:
      sp = vars[2].split('/')
      dur = float(sp[0]) / float(sp[1])
    else:
      dur = float(vars[2])
    if '.' in vars[0]: # it's a chord
      notes = []
      for current_note in vars[0].split('.'):
        new_note = m21.note.Note(current_note, duration = m21.duration.Duration(dur))
        new_note.storedInstrument = i()
        notes.append(new_note)
      new_chord = m21.chord.Chord(notes)
      new_chord.offset = offset
      output_notes.append(new_chord)
    else: # it's a single note
      new_note = m21.note.Note(vars[0], duration = m21.duration.Duration(dur))
      new_note.offset = offset
      new_note.storedInstrument = i()
      output_notes.append(new_note)
    offset += off

  midi_stream = m21.stream.Stream(output_notes)
  midi_stream.write('midi', fp=output)
  # insert the desired instrument
  s = m21.converter.parse(output)
  for p in s.parts:
    p.insert(0, i())
  k = s.analyze('key')
  ivl = m21.interval.Interval(k.tonic, m21.pitch.Pitch(key))
  s = s.transpose(ivl)
  s.write('midi', output)

def generate_json(notes, out_name):
  offset = 0
  response = {}
  output_notes = []
  for chord in notes:
    vars = chord.split('|')
	
    output_notes.append({
      "note" : vars[0],
      "off" : vars[1],
      "dur" : vars[2]
    })
  response['notes'] = output_notes
  response['name'] = out_name
  return json.dumps(response)

def convert_midi(path, target_key=None):
  stream = m21.converter.parse(path)
  parts = m21.instrument.partitionByInstrument(stream)
  key = stream.analyze('key')
  key_str = str(key)
  print('Key detected ' + key_str)
  if target_key != None and key_str != target_key:
    # print('Transposing to ' + target_key)
    # interval = m21.interval.Interval(key.tonic, m21.pitch.Pitch('G'))
    # stream = stream.transpose(interval)
    if key.mode == "major":
      halfSteps = majors[key.tonic.name]
    elif key.mode == "minor":
      halfSteps = minors[key.tonic.name]

    stream = stream.transpose(halfSteps)
    key = stream.analyze('key')
    print('Transposed to ' + str(key))
    print(key.tonic.name + key.mode)
    parts = m21.instrument.partitionByInstrument(stream)
  track = None
  if parts:
    track = parts.parts[0] if len(parts.parts[0].pitches) > 0 else parts.parts[1]
  else:
    track = stream.flat.notes
  notes = []
  offsets = []
  durations = []
  last_offset = 0
  for event in track:
    if isinstance(event, m21.note.Note):
      notes.append(str(event.pitch))
      offsets.append(str(event.offset-last_offset))
      durations.append(event.duration.quarterLength)
    elif isinstance(event, m21.chord.Chord):
      notes.append('.'.join(str(n) for n in event.pitches))
      offsets.append(str(event.offset-last_offset))
      durations.append(event.duration.quarterLength)
    last_offset = event.offset
  print('Converted ' + path)
  return notes, offsets, durations

def get_unique_pitches(track):
  s = set()
  for song in track:
    s.update(set(song))
  return sorted(s)