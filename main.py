# from tensorflow import keras

from music21 import converter


score = converter.parse('./midis/VGM/zelda.mid').chordify()

print(score.show('text'))