import pynbs
import sys
import numpy
import mcschematic
from constants import *


def verify_format(song):
    print('Verifying your song...')
    is_valid = True
    # check song length
    print('Checking song length...')
    if song.header.song_length > MAX_SONG_LENGTH:
        print('Warning: Your song is too long.')
        is_valid = False

    # check custom instruments
    print('Checking for custom instruments...')
    if len(song.instruments) > 0:
        print('Warning: Your song contains custom instruments.')
        is_valid = False

    # check range
    print('Checking note ranges...')
    for note in song.notes:
        if note.key < INSTRUMENT_RANGE[0] or note.key > INSTRUMENT_RANGE[1]:
            print('Warning: Your song contains notes that are outside the normal range.')
            is_valid = False
            break

    # check chord lengths
    print('Checking chord lengths...')
    for tick, chord in song:
        list_of_chords = {}
        for note in chord:
            if note.instrument in list_of_chords:
                list_of_chords[note.instrument].append(note)
            else:
                list_of_chords[note.instrument] = [note]
        for instrument, singleChord in list_of_chords.items():
            lower_octave_notes = []
            upper_octave_notes = []
            for note in singleChord:
                if note.key < INSTRUMENT_RANGE[0] + 12:
                    lower_octave_notes.append(note)
                else:
                    upper_octave_notes.append(note)
            if len(lower_octave_notes) > CHORD_MAX_SIZES[INSTRUMENTS[instrument]] or len(upper_octave_notes) > \
                    CHORD_MAX_SIZES[INSTRUMENTS[instrument]]:
                print('Warning: Your song contains chords that are larger than allowed.')
                is_valid = False
                break
        if not is_valid:
            break

    if not is_valid:
        sys.exit('We found some issues with your song. Please make sure to format it using the "nbs_format_song" script.')
    else:
        print('Song verified. Everything looks good!')


def remove_empty_chests(chest_contents):
    new_chest_contents = {}
    for instrument, contents in chest_contents.items():
        new_chest_contents[instrument] = []
        for octaves in contents:
            new_octaves = [[], []]
            is_lower_octave_empty = 1
            is_upper_octave_empty = 1
            for note in octaves[0]:
                if note != -1:
                    is_lower_octave_empty = 0
                    break
            for note in octaves[1]:
                if note != -1:
                    is_upper_octave_empty = 0
                    break
            if is_lower_octave_empty == 0:
                new_octaves[0] = octaves[0]
            if is_upper_octave_empty == 0:
                new_octaves[1] = octaves[1]
            new_chest_contents[instrument].append(new_octaves)
    return new_chest_contents


def new_disc(slot, note):
    if note == -1:
        return '{Count:1b,Slot:' + str(slot) + 'b,id:"minecraft:wooden_shovel"}'
    if note >= 12:
        note -= 12
    disc = NOTES_TO_DISCS_NAMED[note] if NAME_DISCS == 1 else NOTES_TO_DISCS_UNNAMED[note]
    return '{Count:1b,Slot:' + str(slot) + 'b,id:' + disc + '}'


def create_shulker(current_shulker, contents):
    slot = (current_shulker - 1) % 27
    # remove trailing comma
    contents = contents[:len(contents) - 1]
    return '{Count:1b,Slot:' + str(
        slot) + 'b,id:"minecraft:shulker_box",tag:{BlockEntityTag:{CustomName:\'{"text":"' + str(
        current_shulker) + '"}\',Items:[' + contents + '],id:"minecraft:shulker_box"},display:{Name:\'{"text":"' + str(
        current_shulker) + '"}\'}}}'


def create_chest(type_, contents):
    # remove trailing comma
    if len(contents) > 0:
        contents = contents[:len(contents) - 1]
    return 'minecraft:chest[facing=south,type=' + type_ + ']{Items:[' + contents + ']}'


def create_sign(instrument, current_module, octave):
    octave_message = 'lower octave' if octave == 0 else 'upper octave'
    return 'minecraft:oak_wall_sign[facing=south,waterlogged=false]{front_text:{color:"black",has_glowing_text:0b,messages:[\'{"text":"' + instrument + ' ' + str(
        current_module) + '"}\',\'{"text":"' + octave_message + '"}\',\'{"text":""}\',\'{"text":""}\']},is_waxed:0b}'


def main():
    # get song file from user
    song_file = input('Please enter the file name of your song (include the .nbs): ')
    try:
        song = pynbs.read(song_file)
        song_name = song_file[:song_file.find('.nbs')]
    except Exception as e:
        sys.exit(f'An error occurred while reading the song file "{song_file}".\nExact error (search this up for help): {e}')

    verify_format(song)

    # fix the length of the song for min fill of last chest
    last_chest_fill = (song.header.song_length + 1) % 27
    song_length_adjusted = song.header.song_length + 1
    if 1 <= last_chest_fill < CHEST_MIN_FILL:
        song_length_adjusted += CHEST_MIN_FILL - last_chest_fill

    # initialize data structure
    all_chest_contents = {}
    empty_chest = numpy.full(song_length_adjusted, -1)
    for instrument in INSTRUMENTS:
        all_chest_contents[instrument] = []
        for i in range(CHORD_MAX_SIZES[instrument]):
            all_chest_contents[instrument].append([empty_chest.copy(), empty_chest.copy()])

    # iterate through the whole song by chords
    key_modifier = INSTRUMENT_RANGE[0]
    current_indices = {}
    for tick, chord in song:
        # reset current indices
        for instrument in INSTRUMENTS:
            current_indices[instrument] = [0, 0]

        for note in chord:
            instrument = INSTRUMENTS[note.instrument]
            adjusted_key = note.key - key_modifier
            octave = 0 if adjusted_key <= 11 else 1
            all_chest_contents[instrument][current_indices[instrument][octave]][octave][tick] = adjusted_key
            current_indices[instrument][octave] += 1

    minimal_chest_contents = remove_empty_chests(all_chest_contents)

    # turn minimal_chest_contents into a schematic
    schem = mcschematic.MCSchematic()
    offset = 0
    print('Generating Schematic...')
    for instrument, contents in minimal_chest_contents.items():
        current_module = 1
        for module in contents:
            lower_chest1 = ''
            upper_chest1 = ''
            lower_chest2 = ''
            upper_chest2 = ''
            lower_shulker = ''
            upper_shulker = ''
            current_shulker = 1
            lower_octave_empty = len(module[0]) == 0
            upper_octave_empty = len(module[1]) == 0
            for currentTick in range(song_length_adjusted):
                current_slot = currentTick % 27
                if lower_octave_empty == 0:
                    lower_shulker += new_disc(current_slot, module[0][currentTick]) + ','
                if upper_octave_empty == 0:
                    upper_shulker += new_disc(current_slot, module[1][currentTick]) + ','
                # if we are on the last slot of a shulker box, or the song has ended
                if (currentTick + 1) % 27 == 0 or currentTick == song_length_adjusted - 1:
                    # turn the shulker contents into actual shulker
                    if lower_octave_empty == 0:
                        lower_shulker = create_shulker(current_shulker, lower_shulker)
                    if upper_octave_empty == 0:
                        upper_shulker = create_shulker(current_shulker, upper_shulker)
                    # if the current shulker should go in the first chests
                    if current_shulker <= 27:
                        if lower_octave_empty == 0:
                            lower_chest1 += lower_shulker + ','
                        if upper_octave_empty == 0:
                            upper_chest1 += upper_shulker + ','
                    else:
                        if lower_octave_empty == 0:
                            lower_chest2 += lower_shulker + ','
                        if upper_octave_empty == 0:
                            upper_chest2 += upper_shulker + ','
                    # reset the shulkers and increment the current shulker
                    lower_shulker = ''
                    upper_shulker = ''
                    current_shulker += 1

            if lower_octave_empty == 0:
                lower_chest1 = create_chest('right', lower_chest1)
                lower_chest2 = create_chest('left', lower_chest2)
                schem.setBlock((offset, 0, -1), lower_chest1)
                schem.setBlock((offset + 1, 0, -1), lower_chest2)
                schem.setBlock((offset, 0, 0), create_sign(instrument, current_module, 0))
            else:
                schem.setBlock((offset, 0, -1), "minecraft:air")
                schem.setBlock((offset + 1, 0, -1), "minecraft:air")
                schem.setBlock((offset, 0, 0), "minecraft:air")

            if upper_octave_empty == 0:
                upper_chest1 = create_chest('right', upper_chest1)
                upper_chest2 = create_chest('left', upper_chest2)
                schem.setBlock((offset, 1, -1), upper_chest1)
                schem.setBlock((offset + 1, 1, -1), upper_chest2)
                schem.setBlock((offset, 1, 0), create_sign(instrument, current_module, 1))
            else:
                schem.setBlock((offset, 1, -1), "minecraft:air")
                schem.setBlock((offset + 1, 1, -1), "minecraft:air")
                schem.setBlock((offset, 1, 0), "minecraft:air")

            current_module += 1
            offset += 2

    save_name = song_name.lower().replace('(', '').replace(')', '').replace(' ', '_')
    schem.save('', save_name, mcschematic.Version.JE_1_20)
    print('Your schematic was successfully generated and saved under "' + save_name + '.schem"')


if __name__ == '__main__':
    main()
