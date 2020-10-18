# from tensorflow import keras

import os
import multiprocessing as mp
import music21 as m21

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
      notes.append(event.pitch)
    elif isinstance(event, m21.chord.Chord):
      notes.append('.'.join(str(n) for n in event.pitches))
  print('Converted ' + path)
  return {
    'notes': notes
  }

pool = mp.Pool(mp.cpu_count())

midis_folder = './midis/VGM/'
midi_files = map(lambda f: midis_folder + f, os.listdir(midis_folder))
print('Converting midis...')
songs = pool.map(convert_midi, midi_files)
print('Done')

for note in songs[1]['notes']:
  print(note)