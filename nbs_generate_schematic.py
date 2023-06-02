import pynbs
import sys
import numpy
import mcschematic
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
    sys.exit('We found some issues with your song. Please make sure to format it using the "nbs_format_song" script.')
  else:
    print('Song verified. Everything looks good!')

def removeEmptyChests(chestContents):
  newChestContents = {}
  for instrument, contents in chestContents.items():
    newChestContents[instrument] = []
    for octaves in contents:
      newOctaves = [[], []]
      isLowerOctaveEmpty = 1
      isUpperOctaveEmpty = 1
      for note in octaves[0]:
        if note != -1:
          isLowerOctaveEmpty = 0
          break
      for note in octaves[1]:
        if note != -1:
          isUpperOctaveEmpty = 0
          break
      if isLowerOctaveEmpty == 0:
        newOctaves[0] = octaves[0]
      if isUpperOctaveEmpty == 0:
        newOctaves[1] = octaves[1]
      newChestContents[instrument].append(newOctaves)
  return newChestContents

def newDisc(slot, note):
  if note == -1:
    return '{Count:1b,Slot:' + str(slot) + 'b,id:"minecraft:wooden_shovel"}'
  while note >= 12:
    note -= 12
  return '{Count:1b,Slot:' + str(slot) + 'b,id:' + NOTES_TO_DISCS[note] + '}'

def createShulker(currentShulker, contents):
  slot = (currentShulker - 1) % 27
  # remove trailing comma
  contents = contents[:len(contents) - 1]
  return '{Count:1b,Slot:' + str(slot) + 'b,id:"minecraft:shulker_box",tag:{BlockEntityTag:{CustomName:\'{"text":"' + str(currentShulker) + '"}\',Items:[' + contents + '],id:"minecraft:shulker_box"},display:{Name:\'{"text":"' + str(currentShulker) + '"}\'}}}'

def createChest(type, contents):
  # remove trailing comma
  if len(contents) > 0:
    contents = contents[:len(contents) - 1]
  return 'minecraft:chest[facing=south,type=' + type + ']{Items:[' + contents + ']}'

def createSign(instrument, currentModule, octave):
  octaveMessage = 'lower octave' if octave == 0 else 'upper octave'
  return 'minecraft:oak_wall_sign[facing=south,waterlogged=false]{Color:"black",GlowingText:0b,Text1:\'{"text":"' + instrument + ' ' + str(currentModule) + '"}\',Text2:\'{"text":"' + octaveMessage + '"}\'}'

def main():
   # get song file from user
  songFile = input('Please enter the file name of your song (include the .nbs): ')
  try:
    song = pynbs.read(songFile)
    songName = songFile[:songFile.find('.nbs')]
  except:
    sys.exit('Error: could not find "' + songFile + '"')
  
  verifyFormat(song)

  # fix the length of the song for min fill of last chest
  lastChestFill = (song.header.song_length + 1) % 27
  songLengthAdjusted = song.header.song_length + 1
  if lastChestFill >= 1 and lastChestFill < CHEST_MIN_FILL:
    songLengthAdjusted += CHEST_MIN_FILL - lastChestFill

  # initialize data structure
  allChestContents = {}
  emptyChest = numpy.full(songLengthAdjusted, -1)
  for instrument in INSTRUMENTS:
    allChestContents[instrument] = []
    for i in range(CHORD_MAX_SIZES[instrument]):
      allChestContents[instrument].append([emptyChest.copy(), emptyChest.copy()])

  # iterate through the whole song by chords
  keyModifier = INSTRUMENT_RANGE[0]
  currentIndices = {}
  for tick, chord in song:
    # reset current indices
    for instrument in INSTRUMENTS:
      currentIndices[instrument] = 0
    
    for note in chord:
      instrument = INSTRUMENTS[note.instrument]
      adjustedKey = note.key - keyModifier
      octave = 0 if adjustedKey <= 11 else 1
      allChestContents[instrument][currentIndices[instrument]][octave][tick] = adjustedKey
      currentIndices[instrument] += 1
  
  minimalChestContents = removeEmptyChests(allChestContents)

  # turn minimalChestContents into a schematic
  schem = mcschematic.MCSchematic()
  offset = 0
  print('Generating Schematic...')
  for instrument, contents in minimalChestContents.items():
    currentModule = 1
    for module in contents:
      lowerChest1 = ''
      upperChest1 = ''
      lowerChest2 = ''
      upperChest2 = ''
      lowerShulker = ''
      upperShulker = ''
      currentShulker = 1
      lowerOctaveEmpty = len(module[0]) == 0
      upperOctaveEmpty = len(module[1]) == 0
      for currentTick in range(songLengthAdjusted):
        currentSlot = currentTick % 27
        if lowerOctaveEmpty == 0:
          lowerShulker += newDisc(currentSlot, module[0][currentTick]) + ','
        if upperOctaveEmpty == 0:
          upperShulker += newDisc(currentSlot, module[1][currentTick]) + ','
        # if we are on the last slot of a shulker box, or the song has ended
        if (currentTick + 1) % 27 == 0 or currentTick == songLengthAdjusted - 1:
          # turn the shulker contents into actual shulker
          if lowerOctaveEmpty == 0:
            lowerShulker = createShulker(currentShulker, lowerShulker)
          if upperOctaveEmpty == 0:
            upperShulker = createShulker(currentShulker, upperShulker)
          # if the current shulker should go in the first chests
          if currentShulker <= 27:
            if lowerOctaveEmpty == 0:
              lowerChest1 += lowerShulker + ','
            if upperOctaveEmpty == 0:
              upperChest1 += upperShulker + ','
          else:
            if lowerOctaveEmpty == 0:
              lowerChest2 += lowerShulker + ','
            if upperOctaveEmpty == 0:
              upperChest2 += upperShulker + ','
          # reset the shulkers and increment the current shulker
          lowerShulker = ''
          upperShulker = ''
          currentShulker += 1
      
      if lowerOctaveEmpty == 0:
        lowerChest1 = createChest('right', lowerChest1)
        lowerChest2 = createChest('left', lowerChest2)
        schem.setBlock((offset, 0, -1), lowerChest1)
        schem.setBlock((offset + 1, 0, -1), lowerChest2)
        schem.setBlock((offset, 0, 0), createSign(instrument, currentModule, 0))
      if upperOctaveEmpty == 0:
        upperChest1 = createChest('right', upperChest1)
        upperChest2 = createChest('left', upperChest2)
        schem.setBlock((offset, 1, -1), upperChest1)
        schem.setBlock((offset + 1, 1, -1), upperChest2)
        schem.setBlock((offset, 1, 0), createSign(instrument, currentModule, 1))
      
      currentModule += 1
      if lowerOctaveEmpty == 0 or upperOctaveEmpty == 0:
        offset += 2
  
  saveName = songName.lower().replace('(', '').replace(')', '').replace(' ', '_')
  schem.save('', saveName, mcschematic.Version.JE_1_19)
  print('Your schematic was successfully generated and saved under "' + saveName + '.schem"')


if __name__ == '__main__':
  main()
