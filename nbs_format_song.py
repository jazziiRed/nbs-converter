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

def main():
  # get song file from user
  songFile = input('Please enter the file name of your song (include the .nbs): ')
  try:
    song = pynbs.read(songFile)
  except:
    sys.exit('Error: could not find \"' + songFile + '\"')

  # give user option to compress song
  originalSongLength = song.header.song_length
  if originalSongLength > 1458:
    print('Your song\'s length is ', originalSongLength, ', and the max length of a song is ', MAX_SONG_LENGTH, '.')
  print('Compressing your song would remove every other tick and make it half as long. This may or may not make your song sound much worse.')
  setting_compress = 1 if getValidInput(['y', 'n'], 'Would you like to compress your song? (y/n): ') else 0

  # warn user if there are notes out of range
  for note in song.notes:
    if note.key < INSTRUMENT_RANGE[0] | note.key > INSTRUMENT_RANGE[1]:
      print('Your song contains notes that are outside the normal range. They will be transposed to be playable.')
      input('Press Enter to Continue')
      break
  
  # warn user if there are custom instruments
  if len(song.instruments) > 0:
    print('Your song contains custom instruments. All notes using custom instruments will be removed.')
    input('Press Enter to Continue')


if __name__ == '__main__':
  main()
