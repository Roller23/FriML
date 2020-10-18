# from tensorflow import keras

import os
import multiprocessing
from music21 import converter, instrument
from multiprocessing import Pool

def convert_midi(path):
  score = converter.parse(path).chordify()
  print('Converted ' + path)
  return score

pool = Pool(multiprocessing.cpu_count())

midis_folder = './midis/VGM/'
midi_files = map(lambda f: midis_folder + f, os.listdir(midis_folder))
print('Converting midis...')
scores = pool.map(convert_midi, midi_files)
print('Done\n', scores)

# print(score.show('text'))