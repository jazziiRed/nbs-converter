import pynbs
import sys
import numpy
from constants import *

def verifyFormat(song):
  print('Verifying your song...')
  isValid = 1
  # check song length
  print('Checking song length...')
  if song.header.song_length > MAX_SONG_LENGTH:
    print('Warning: Your song is too long.')
    isValid = 0
  
  # check custom instruments
  print('Checking for custom instruments...')
  if len(song.instruments) > 0:
    print('Warning: Your song contains custom instruments.')
    isValid = 0

  # check range
  print('Checking note ranges...')
  for note in song.notes:
    if note.key < INSTRUMENT_RANGE[0] or note.key > INSTRUMENT_RANGE[1]:
      print('Warning: Your song contains notes that are outside the normal range.')
      isValid = 0
      break

  # check chord lengths
  print('Checking chord lengths...')
  for tick, chord in song:
    listOfChords = {}
    for note in chord:
      if note.instrument in listOfChords:
        listOfChords[note.instrument].append(note)
      else:
        listOfChords[note.instrument] = [note]
    for instrument, singleChord in listOfChords.items():
      if len(singleChord) > CHORD_MAX_SIZES[INSTRUMENTS[instrument]]:
        print('Warning: Your song contains chords that are larger than allowed.')
        isValid = 0
        break
    if isValid == 0:
      break

  if isValid == 0:
    sys.exit('We found some issues with your song. Please make sure to format it using the \"nbs_format_song\" script.')
  else:
    print('Song verified. Everything looks good!')

def removeEmptyChests(chestContents):
  newChestContents = {}
  for instrument, contents in chestContents.items():
    newChestContents[instrument] = []
    for chest in contents:
      isEmpty = 1
      for note in chest:
        if note != -1:
          isEmpty = 0
          break
      if isEmpty == 0:
        newChestContents[instrument].append(chest)
  return newChestContents

def main():
   # get song file from user
  songFile = input('Please enter the file name of your song (include the .nbs): ')
  try:
    song = pynbs.read(songFile)
    songName = songFile[:songFile.find('.nbs')]
  except:
    sys.exit('Error: could not find \"' + songFile + '\"')
  
  verifyFormat(song)

  # fix the length of the song for min fill of last chest
  lastChestFill = (song.header.song_length + 1) % 27
  songLengthAdjusted = song.header.song_length + 1
  if lastChestFill >= 1 and lastChestFill < CHEST_MIN_FILL:
    songLengthAdjusted += CHEST_MIN_FILL - lastChestFill

  # initialize data structure
  allChestContents = {}
  for instrument in INSTRUMENTS:
    allChestContents[instrument] = numpy.full((CHORD_MAX_SIZES[instrument], songLengthAdjusted), -1)

  # iterate through the whole song by chords
  keyModifier = INSTRUMENT_RANGE[0]
  currentIndices = {}
  for tick, chord in song:
    # reset current indices
    for instrument in INSTRUMENTS:
      currentIndices[instrument] = 0
    
    for note in chord:
      instrument = INSTRUMENTS[note.instrument]
      allChestContents[instrument][currentIndices[instrument]][tick] = note.key - keyModifier
      currentIndices[instrument] += 1
  
  minimalChestContents = removeEmptyChests(allChestContents)

  # todo: turn minimalChestContents into a schematic


if __name__ == '__main__':
  main()
