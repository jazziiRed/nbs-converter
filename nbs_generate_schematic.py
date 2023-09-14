import pynbs
import sys
import numpy
import mcschematic
from constants import *


def verifyFormat(song, songName):
  print('Verifying your song...')
  isValid = True
  # check song length
  print('Checking song length...')
  if song.header.song_length > MAX_SONG_LENGTH:
    print('Warning: Your song is too long.')
    isValid = False

  # check custom instruments
  print('Checking for custom instruments...')
  if len(song.instruments) > 0:
    print('Warning: Your song contains custom instruments.')
    isValid = False

  # check range
  print('Checking note ranges...')
  for note in song.notes:
    if note.key < INSTRUMENT_RANGE[0] or note.key > INSTRUMENT_RANGE[1]:
      print('Warning: Your song contains notes that are outside the normal range.')
      isValid = False
      break

  # check chord lengths
  print('Checking chord lengths...')
  for tick, chord in song:
    listOfChords = {}
    for note in chord:
      instrument = note.instrument
      if instrument in listOfChords:
        listOfChords[instrument].append(note)
      else:
        listOfChords[instrument] = [note]

    for instrument, singleChord in listOfChords.items():
      lowerOctaveNotes = [note for note in singleChord if note.key < INSTRUMENT_RANGE[0] + 12]
      upperOctaveNotes = [note for note in singleChord if note.key >= INSTRUMENT_RANGE[0] + 12]

      if len(lowerOctaveNotes) > CHORD_MAX_SIZES[INSTRUMENTS[instrument]] or len(upperOctaveNotes) > CHORD_MAX_SIZES[INSTRUMENTS[instrument]]:
        print('Warning: Your song contains chords that are larger than allowed.')
        isValid = False
        break

    if not isValid:
      break

  if not isValid:
    sys.exit(f'We found some issues with your song "{songName}". Please make sure to format it using the "nbs_format_song" script.')
  else:
    print('Song verified. Everything looks good!')


def removeEmptyChests(chestContents):
  newChestContents = {}

  for instrument, contents in chestContents.items():
    newChestContents[instrument] = []

    for octaves in contents:
      newOctaves = [[], []]

      isLowerOctaveNotEmpty = any(note != -1 for note in octaves[0])
      isUpperOctaveNotEmpty = any(note != -1 for note in octaves[1])

      if isLowerOctaveNotEmpty:
        newOctaves[0] = octaves[0]

      if isUpperOctaveNotEmpty:
        newOctaves[1] = octaves[1]

      newChestContents[instrument].append(newOctaves)

  return newChestContents


def newDisc(slot, note):
  if note == -1:
    return '{Count:1b,Slot:' + str(slot) + 'b,id:"minecraft:wooden_shovel"}'

  if note >= 12:
    note -= 12

  disc = NOTES_TO_DISCS_NAMED[note] if NAME_DISCS else NOTES_TO_DISCS_UNNAMED[note]
  return '{Count:1b,Slot:' + str(slot) + 'b,id:' + disc + '}'


def createShulker(currentShulker, contents):
  slot = (currentShulker - 1) % 27

  # remove trailing comma
  contents = contents[:len(contents) - 1]
  return '{Count:1b,Slot:' + str(
    slot) + 'b,id:"minecraft:shulker_box",tag:{BlockEntityTag:{CustomName:\'{"text":"' + str(
    currentShulker) + '"}\',Items:[' + contents + '],id:"minecraft:shulker_box"},display:{Name:\'{"text":"' + str(
    currentShulker) + '"}\'}}}'


def createChest(type_, contents):
  # remove trailing comma
  if len(contents) > 0:
    contents = contents[:len(contents) - 1]

  return 'minecraft:chest[facing=south,type=' + type_ + ']{Items:[' + contents + ']}'


def createSign(instrument, currentModule, octave):
  octaveMessage = 'lower octave' if octave == 0 else 'upper octave'
  return 'minecraft:oak_wall_sign[facing=south,waterlogged=false]{front_text:{color:"black",has_glowing_text:0b,messages:[\'{"text":"' + instrument + ' ' + str(
    currentModule) + '"}\',\'{"text":"' + octaveMessage + '"}\',\'{"text":""}\',\'{"text":""}\']},is_waxed:0b}'


def main():
  # get song file from user
  songFile = input('Please enter the file name of your song (include the .nbs): ')
  if not songFile.endswith('.nbs'):
    sys.exit('Your song file must end with ".nbs".')

  try:
    song = pynbs.read(songFile)
    songName = songFile[:-4]
  except Exception as e:
    sys.exit(f'An error occurred while reading the song file "{songFile}".\nError name: {e.__class__.__name__}\nExact error (search this up for help): {e}')

  verifyFormat(song, songName)

  # fix the length of the song for min fill of last chest
  lastChestFill = (song.header.song_length + 1) % 27
  songLengthAdjusted = song.header.song_length + 1
  if 1 <= lastChestFill < CHEST_MIN_FILL:
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
      currentIndices[instrument] = [0, 0]

    for note in chord:
      instrument = INSTRUMENTS[note.instrument]
      adjustedKey = note.key - keyModifier
      octave = 0 if adjustedKey <= 11 else 1
      allChestContents[instrument][currentIndices[instrument][octave]][octave][tick] = adjustedKey
      currentIndices[instrument][octave] += 1

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

        if not lowerOctaveEmpty:
          lowerShulker += newDisc(currentSlot, module[0][currentTick]) + ','

        if not upperOctaveEmpty:
          upperShulker += newDisc(currentSlot, module[1][currentTick]) + ','

        # if we are on the last slot of a shulker box, or the song has ended
        if (currentTick + 1) % 27 == 0 or currentTick == songLengthAdjusted - 1:
          # turn the shulker contents into actual shulker
          if not lowerOctaveEmpty:
            lowerShulker = createShulker(currentShulker, lowerShulker)

          if not upperOctaveEmpty:
            upperShulker = createShulker(currentShulker, upperShulker)

          # if the current shulker should go in the first chests
          if currentShulker <= 27:
            if not lowerOctaveEmpty:
              lowerChest1 += lowerShulker + ','

            if not upperOctaveEmpty:
              upperChest1 += upperShulker + ','

          else:
            if not lowerOctaveEmpty:
              lowerChest2 += lowerShulker + ','

            if not upperOctaveEmpty:
              upperChest2 += upperShulker + ','

          # reset the shulkers and increment the current shulker
          lowerShulker = ''
          upperShulker = ''
          currentShulker += 1

      if not lowerOctaveEmpty:
        lowerChest1 = createChest('right', lowerChest1)
        lowerChest2 = createChest('left', lowerChest2)
        schem.setBlock((offset, 0, -1), lowerChest1)
        schem.setBlock((offset + 1, 0, -1), lowerChest2)
        schem.setBlock((offset, 0, 0), createSign(instrument, currentModule, 0))
      else:
        schem.setBlock((offset, 0, -1), "minecraft:air")
        schem.setBlock((offset + 1, 0, -1), "minecraft:air")
        schem.setBlock((offset, 0, 0), "minecraft:air")

      if not upperOctaveEmpty:
        upperChest1 = createChest('right', upperChest1)
        upperChest2 = createChest('left', upperChest2)
        schem.setBlock((offset, 1, -1), upperChest1)
        schem.setBlock((offset + 1, 1, -1), upperChest2)
        schem.setBlock((offset, 1, 0), createSign(instrument, currentModule, 1))
      else:
        schem.setBlock((offset, 1, -1), "minecraft:air")
        schem.setBlock((offset + 1, 1, -1), "minecraft:air")
        schem.setBlock((offset, 1, 0), "minecraft:air")

      currentModule += 1
      offset += 2

  saveName = songName.lower().replace('(', '').replace(')', '').replace(' ', '_')
  schem.save('', saveName, mcschematic.Version.JE_1_20)
  print('Your schematic was successfully generated and saved under "' + saveName + '.schem"')


if __name__ == '__main__':
  main()
