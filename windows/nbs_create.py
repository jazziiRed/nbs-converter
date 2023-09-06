import pynbs
import sys
from constants import *
import numpy
import mcschematic
import os

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
      lowerOctaveNotes = []
      upperOctaveNotes = []
      for note in singleChord:
        if note.key < INSTRUMENT_RANGE[0] + 12:
          lowerOctaveNotes.append(note)
        else:
          upperOctaveNotes.append(note)
      if len(lowerOctaveNotes) > CHORD_MAX_SIZES[INSTRUMENTS[instrument]] or len(upperOctaveNotes) > CHORD_MAX_SIZES[INSTRUMENTS[instrument]]:
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
  if note >= 12:
    note -= 12
  disc = NOTES_TO_DISCS_NAMED[note] if NAME_DISCS == 1 else NOTES_TO_DISCS_UNNAMED[note]
  return '{Count:1b,Slot:' + str(slot) + 'b,id:' + disc + '}'

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
  return 'minecraft:oak_wall_sign[facing=south,waterlogged=false]{front_text:{color:"black",has_glowing_text:0b,messages:[\'{"text":"' + instrument + ' ' + str(currentModule) + '"}\',\'{"text":"' + octaveMessage + '"}\',\'{"text":""}\',\'{"text":""}\']},is_waxed:0b}'


def getValidInput(validInputs, msg):
  isValid = 0
  while not isValid:
    userInput = input(msg)
    if userInput in validInputs:
      isValid = 1
    else:
      print('"', userInput, '" is not a valid input.')
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

def removeHighestHelper(chord, chordMaxSize):
  if len(chord) <= chordMaxSize:
    return chord
  highestNote = chord[0]
  for note in chord:
    if note.key > highestNote.key:
      highestNote = note
  chord.remove(highestNote)
  return removeHighestHelper(chord, chordMaxSize)

def removeHighestNotes(chord, chordMaxSize):
  lowerOctaveNotes = upperOctaveNotes = []
  for note in chord:
    if note.key < INSTRUMENT_RANGE[0] + 12:
      lowerOctaveNotes.append(note)
    else:
      upperOctaveNotes.append(note)
  lowerOctaveNotes = removeHighestHelper(lowerOctaveNotes, chordMaxSize)
  upperOctaveNotes = removeHighestHelper(upperOctaveNotes, chordMaxSize)
  return lowerOctaveNotes + upperOctaveNotes

def removeLowestHelper(chord, chordMaxSize):
  if len(chord) <= chordMaxSize:
    return chord
  lowestNote = chord[0]
  for note in chord:
    if note.key < lowestNote.key:
      lowestNote = note
  chord.remove(lowestNote)
  return removeLowestHelper(chord, chordMaxSize)

def removeLowestNotes(chord, chordMaxSize):
  lowerOctaveNotes = []
  upperOctaveNotes = []
  for note in chord:
    if note.key < INSTRUMENT_RANGE[0] + 12:
      lowerOctaveNotes.append(note)
    else:
      upperOctaveNotes.append(note)
  lowerOctaveNotes = removeLowestHelper(lowerOctaveNotes, chordMaxSize)
  upperOctaveNotes = removeLowestHelper(upperOctaveNotes, chordMaxSize)
  return lowerOctaveNotes + upperOctaveNotes

def removeChordViolations(chord):
  listOfChords = {}
  for note in chord:
    if note.instrument in listOfChords:
      listOfChords[note.instrument].append(note)
    else:
      listOfChords[note.instrument] = [note]
  newChord = []
  for instrument, singleChord in listOfChords.items():
    if KEEP_NOTES_BY_INSTRUMENT[INSTRUMENTS[instrument]] == 'h':
      newSingleChord = removeLowestNotes(singleChord, CHORD_MAX_SIZES[INSTRUMENTS[instrument]])
    else:
      newSingleChord = removeHighestNotes(singleChord, CHORD_MAX_SIZES[INSTRUMENTS[instrument]])
    newChord += newSingleChord
  
  # We need to preserve the original note order, because sometimes
  # saving has issues when notes are reordered
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
    sys.exit('Error: could not find "' + songFile + '"')

  # give user option to compress song
  originalSongLength = song.header.song_length
  if originalSongLength > MAX_SONG_LENGTH:
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
    print('Notice: Your song contained chords that were larger than allowed. Some notes were removed from these chords.')

  # save the new song
  newFileName = songName + ' (Formatted).nbs'

  newSong.save(newFileName)
  print('Your formatted song was saved under "', newFileName, '"')




  absolute_file_path = os.path.join(os.path.dirname(__file__), newFileName)
  songFile = newFileName
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
      else:
        schem.setBlock((offset, 0, -1), "minecraft:air")
        schem.setBlock((offset + 1, 0, -1), "minecraft:air")
        schem.setBlock((offset, 0, 0), "minecraft:air")
      
      if upperOctaveEmpty == 0:
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
  try:
      if getValidInput(['y', 'n'], 'Do you want to keep the formatted .nbs file? (y/n): ') == 'n':
        os.remove(absolute_file_path)
      else:
        print("Proceeding without deletion")
  except Exception as e:
      print(f"Error deleting file: {e}")

if __name__ == '__main__':
  main()
