import pynbs
import sys
from constants import *


def getValidInput(validInputs, prompt):
    while True:
        userInput = input(prompt)
        if userInput in validInputs:
            return userInput
        else:
            print(f'"{userInput}" is not a valid input. Please try again.')


def removeCustomNotes(chord):
    return [note for note in chord if note.instrument <= 15]


def fixIllegalNotes(chord):
    instrumentMin, instrumentMax = INSTRUMENT_RANGE
    newChord = []

    for note in chord:
        while note.key < instrumentMin:
            note.key += 12
        while note.key > instrumentMax:
            note.key -= 12
        newChord.append(note)

    return newChord


def removeHighestHelper(chord, chordMaxSize):
    if len(chord) <= chordMaxSize:
        return chord

    highestNote = max(chord, key=lambda note: note.key)
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

    lowestNote = min(chord, key=lambda note: note.key)
    chord.remove(lowestNote)

    return removeLowestHelper(chord, chordMaxSize)


def removeLowestNotes(chord, chord_max_size):
    lowerOctaveNotes = [note for note in chord if note.key < INSTRUMENT_RANGE[0] + 12]
    upperOctaveNotes = [note for note in chord if note.key >= INSTRUMENT_RANGE[0] + 12]

    lowerOctaveNotes = removeLowestHelper(lowerOctaveNotes, chord_max_size)
    upperOctaveNotes = removeLowestHelper(upperOctaveNotes, chord_max_size)

    return lowerOctaveNotes + upperOctaveNotes


def removeChordViolations(chord):
    listOfChords = {}
    for note in chord:
        instrument = note.instrument
        if instrument in listOfChords:
            listOfChords[instrument].append(note)
        else:
            listOfChords[instrument] = [note]

    newChord = []
    for instrument, singleChord in listOfChords.items():
        maxSize = CHORD_MAX_SIZES[INSTRUMENTS[instrument]]

        if KEEP_NOTES_BY_INSTRUMENT[INSTRUMENTS[instrument]] == 'h':
            newSingleChord = removeLowestNotes(singleChord, maxSize)
        else:
            newSingleChord = removeHighestNotes(singleChord, maxSize)

        newChord.extend(newSingleChord)

    # We need to preserve the original note order, because sometimes
    # saving has issues when notes are reordered
    preservedOrderChord = [note for note in chord if note in newChord]

    return preservedOrderChord, len(preservedOrderChord) < len(chord)


def main(songFile):
    if not songFile.endswith('.nbs'):
        sys.exit('Your song file must end with ".nbs".')

    try:
        song = pynbs.read(songFile)
        songName = songFile[:-4]
    except Exception as e:
        sys.exit(f'An error occurred while reading the song file "{songFile}".\nError name: {e.__class__.__name__}\nExact error (search this up for help): {e}')

    # give user option to compress song
    originalSongLength = song.header.song_length
    if originalSongLength > MAX_SONG_LENGTH:
        print(f"Your song's length is {originalSongLength}, and the max length of a song is {MAX_SONG_LENGTH}.")

    print('You might want to compress your song if it is too slow or too long.')
    print('Compressing your song would remove every other tick and make it half as long. This may or may not make your song sound much worse.')
    settingCompress = True if getValidInput(['y', 'n'], 'Would you like to compress your song? (y/n): ') == 'y' else False

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

    hasMaxChordViolation = False

    # iterate through the whole song by chords
    for tick, chord in song:
        newTick = tick if not settingCompress else tick // 2

        if newTick > MAX_SONG_LENGTH:
            print('Notice: Your song was too long, so some had to be cut off the end.')
            break

        if (tick % 2 != 0 and not settingCompress) or (tick % 2 == 0):
            chord = removeCustomNotes(chord)
            chord = fixIllegalNotes(chord)
            chord, chordViolation = removeChordViolations(chord)

            if chordViolation:
                hasMaxChordViolation = True

            for note in chord:
                note.tick = newTick
                note.panning = 0
                note.pitch = 0
                newSong.notes.append(note)

    if hasMaxChordViolation:
        print('Notice: Your song contained chords that were larger than allowed. Some notes were removed from these chords.')

    # save the new song
    newFileName = songName + ' (Formatted).nbs'

    newSong.save(newFileName)
    print(f'Your formatted song was saved under "{newFileName}"')


if __name__ == '__main__':
    main(input('Please enter the file name of your song (include the .nbs): '))
