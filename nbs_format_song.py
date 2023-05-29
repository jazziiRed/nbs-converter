import pynbs
import sys
from constants import *

def getValidInput(validInputs, msg):
  isValid = 0
  while not isValid:
    userInput = input(msg)
    if userInput in validInputs:
      isValid = 1
    else:
      print('\"', userInput, '\" is not a valid input.')
  return userInput

def removeCustomNotes(chord):
  newChord = []
  for note in chord:
    if note.instrument <= 15:
      newChord.append(note)
  return newChord

def fixIllegalNotes(chord):
  newChord = []
  for note in chord:
    if note.key < INSTRUMENT_RANGE[0]:
      while note.key < INSTRUMENT_RANGE[0]:
        note.key += 12
    elif note.key > INSTRUMENT_RANGE[1]:
      while note.key > INSTRUMENT_RANGE[1]:
        note.key -= 12
    newChord.append(note)
  return newChord

def removeHighestNotes(chord, chordMaxSize):
  if len(chord) <= chordMaxSize:
    return chord
  highestNote = chord[0]
  for note in chord:
    if note.key > highestNote.key:
      highestNote = note
  chord.remove(highestNote)
  return removeHighestNotes(chord, chordMaxSize)

def removeChordViolations(chord):
  listOfChords = {}
  for note in chord:
    if note.instrument in listOfChords:
      listOfChords[note.instrument].append(note)
    else:
      listOfChords[note.instrument] = [note]
  newChord = []
  for instrument, singleChord in listOfChords.items():
    newSingleChord = removeHighestNotes(singleChord, CHORD_MAX_SIZES[INSTRUMENTS[instrument]])
    newChord += newSingleChord
  preservedOrderChord = []
  for note in chord:
    if note in newChord:
      preservedOrderChord.append(note)
  return [preservedOrderChord, len(preservedOrderChord) < len(chord)]

def main():
  # get song file from user
  songFile = input('Please enter the file name of your song (include the .nbs): ')
  try:
    song = pynbs.read(songFile)
    songName = songFile[:songFile.find('.nbs')]
  except:
    sys.exit('Error: could not find \"' + songFile + '\"')

  # give user option to compress song
  originalSongLength = song.header.song_length
  if originalSongLength > 1458:
    print('Your song\'s length is ', originalSongLength, ', and the max length of a song is ', MAX_SONG_LENGTH, '.')
  print('You might want to compress your song if it is too slow or too long.')
  print('Compressing your song would remove every other tick and make it half as long. This may or may not make your song sound much worse.')
  settingCompress = 1 if getValidInput(['y', 'n'], 'Would you like to compress your song? (y/n): ') == 'y' else 0

  # warn user if there are notes out of range
  for note in song.notes:
    if note.key < INSTRUMENT_RANGE[0] or note.key > INSTRUMENT_RANGE[1]:
      print('Your song contains notes that are outside the normal range. They will be transposed to be playable.')
      input('Press Enter to Continue')
      break
  
  # warn user if there are custom instruments
  if len(song.instruments) > 0:
    print('Your song contains custom instruments. All notes using custom instruments will be removed.')
    input('Press Enter to Continue')
  
  newSong = pynbs.new_file()
  newSong.header = song.header
  newSong.layers = song.layers
  newSong.header.tempo = 5

  hasMaxChordViolation = 0

  # iterate through the whole song by chords
  for tick, chord in song:
    newTick = tick
    if settingCompress == 1:
      newTick = tick // 2
    if newTick > MAX_SONG_LENGTH:
      print('Notice: Your song was too long, so some had to be cut off the end.')
      break
    if (tick % 2 != 0 and settingCompress == 0) or (tick %2 == 0):
      chord = removeCustomNotes(chord)
      chord = fixIllegalNotes(chord)
      [chord, chordViolation] = removeChordViolations(chord)
      if chordViolation == 1:
        hasMaxChordViolation = 1
      for note in chord:
        note.tick = newTick
        note.panning = 0
        note.pitch = 0
        newSong.notes.append(note)
  
  if hasMaxChordViolation == 1:
    print('Notice: Your song contained chords that were larger than allowed. The highest notes of these chords were removed.')

  #save the new song
  newFileName = songName + ' (Formatted).nbs'

  newSong.save(newFileName)
  print('Your formatted song was saved under \"', newFileName, '\"')


if __name__ == '__main__':
  main()
