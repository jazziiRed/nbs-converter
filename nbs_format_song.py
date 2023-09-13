import pynbs
import sys
from constants import *


def get_valid_input(valid_inputs, prompt):
    while True:
        user_input = input(prompt)
        if user_input in valid_inputs:
            return user_input
        else:
            print(f'"{user_input}" is not a valid input. Please try again.')


def remove_custom_notes(chord):
    return [note for note in chord if note.instrument <= 15]


def fix_illegal_notes(chord):
    instrument_min, instrument_max = INSTRUMENT_RANGE
    new_chord = []

    for note in chord:
        while note.key < instrument_min:
            note.key += 12
        while note.key > instrument_max:
            note.key -= 12
        new_chord.append(note)

    return new_chord


def remove_highest_helper(chord, chord_max_size):
    if len(chord) <= chord_max_size:
        return chord

    highest_note = max(chord, key=lambda note: note.key)
    chord.remove(highest_note)

    return remove_highest_helper(chord, chord_max_size)


def remove_highest_notes(chord, chord_max_size):
    lower_octave_notes = upper_octave_notes = []
    for note in chord:
        if note.key < INSTRUMENT_RANGE[0] + 12:
            lower_octave_notes.append(note)
        else:
            upper_octave_notes.append(note)

    lower_octave_notes = remove_highest_helper(lower_octave_notes, chord_max_size)
    upper_octave_notes = remove_highest_helper(upper_octave_notes, chord_max_size)

    return lower_octave_notes + upper_octave_notes


def remove_lowest_helper(chord, chord_max_size):
    if len(chord) <= chord_max_size:
        return chord

    lowest_note = min(chord, key=lambda note: note.key)
    chord.remove(lowest_note)

    return remove_lowest_helper(chord, chord_max_size)


def remove_lowest_notes(chord, chord_max_size):
    lower_octave_notes = [note for note in chord if note.key < INSTRUMENT_RANGE[0] + 12]
    upper_octave_notes = [note for note in chord if note.key >= INSTRUMENT_RANGE[0] + 12]

    lower_octave_notes = remove_lowest_helper(lower_octave_notes, chord_max_size)
    upper_octave_notes = remove_lowest_helper(upper_octave_notes, chord_max_size)

    return lower_octave_notes + upper_octave_notes


def remove_chord_violations(chord):
    list_of_chords = {}
    for note in chord:
        instrument = note.instrument
        if instrument in list_of_chords:
            list_of_chords[instrument].append(note)
        else:
            list_of_chords[instrument] = [note]

    new_chord = []
    for instrument, singleChord in list_of_chords.items():
        max_size = CHORD_MAX_SIZES[INSTRUMENTS[instrument]]

        if KEEP_NOTES_BY_INSTRUMENT[INSTRUMENTS[instrument]] == 'h':
            new_single_chord = remove_lowest_notes(singleChord, max_size)
        else:
            new_single_chord = remove_highest_notes(singleChord, max_size)

        new_chord.extend(new_single_chord)

    # We need to preserve the original note order, because sometimes
    # saving has issues when notes are reordered
    preserved_order_chord = [note for note in chord if note in new_chord]

    return preserved_order_chord, len(preserved_order_chord) < len(chord)


def main(song_file):
    if not song_file.endswith('.nbs'):
        sys.exit('Your song file must end with ".nbs".')

    try:
        song = pynbs.read(song_file)
        song_name = song_file[:-4]
    except Exception as e:
        sys.exit(f'An error occurred while reading the song file "{song_file}".\nError name: {e.__class__.__name__}\nExact error (search this up for help): {e}')

    # give user option to compress song
    original_song_length = song.header.song_length
    if original_song_length > MAX_SONG_LENGTH:
        print(f"Your song's length is {original_song_length}, and the max length of a song is {MAX_SONG_LENGTH}.")

    print('You might want to compress your song if it is too slow or too long.')
    print('Compressing your song would remove every other tick and make it half as long. This may or may not make your song sound much worse.')
    setting_compress = True if get_valid_input(['y', 'n'], 'Would you like to compress your song? (y/n): ') == 'y' else False

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

    new_song = pynbs.new_file()
    new_song.header = song.header
    new_song.layers = song.layers
    new_song.header.tempo = 5

    has_max_chord_violation = False

    # iterate through the whole song by chords
    for tick, chord in song:
        new_tick = tick if not setting_compress else tick // 2

        if new_tick > MAX_SONG_LENGTH:
            print('Notice: Your song was too long, so some had to be cut off the end.')
            break

        if (tick % 2 != 0 and not setting_compress) or (tick % 2 == 0):
            chord = remove_custom_notes(chord)
            chord = fix_illegal_notes(chord)
            chord, chord_violation = remove_chord_violations(chord)

            if chord_violation:
                has_max_chord_violation = True

            for note in chord:
                note.tick = new_tick
                note.panning = 0
                note.pitch = 0
                new_song.notes.append(note)

    if has_max_chord_violation:
        print('Notice: Your song contained chords that were larger than allowed. Some notes were removed from these chords.')

    # save the new song
    new_file_name = song_name + ' (Formatted).nbs'

    new_song.save(new_file_name)
    print(f'Your formatted song was saved under "{new_file_name}"')


if __name__ == '__main__':
    main(input('Please enter the file name of your song (include the .nbs): '))
