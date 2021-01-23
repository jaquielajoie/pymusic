from mido import MidiFile
import mido
import base64
from mido import Message
from mido.frozen import freeze_message, thaw_message
from mido.frozen import FrozenMessage
from mido import Message, MidiFile, MidiTrack
import math
import random

mido.set_backend('mido.backends.rtmidi')
port = mido.open_output('IAC Driver Bus 1')

arg = input('What midi file do you want to use?')
mid = MidiFile('../'+arg)

pulse = 32
rhythmic = 7
EIGHTH_NOTE_TICKS = 480 #480 = eighth note in Logic (768 in Cubase)
BEAT_VALUE = EIGHTH_NOTE_TICKS
BAR_LENGTH = 4 * BEAT_VALUE
MEASURE_NUMBER = 1
DOWN_BEAT_ON_ONE_X_MEASURES = 4 #How many measures between absolute downbeat on 1
QUANTIZATOIN = [{f'1/{math.floor(8*x)}': math.floor(EIGHTH_NOTE_TICKS//x)} for x in [48,24,16,12,8,4,3,2,1.5,1,0.5,0.25,0.125]]
BPM = mido.bpm2tempo(int(input('What BPM do you want to use?')))
POLYPHONY = 3
MAX_NOTE_LENGTH = QUANTIZATOIN[10]['1/4']
MIN_NOTE_LENGTH = QUANTIZATOIN[4]['1/64']

ORDER = 2

frozen_messages = []
#ngram_messages = {}
note_map = {}
vel_map = {}

for i, track in enumerate(mid.tracks):
    #print('Track {}: {}'.format(i, track.name))
    frozen_messages.append([])
    for msg in track:
        if msg.type == msg.type: #'note_on':
#        if not msg.is_meta:
            print(msg)
        #if msg.type == 'set_tempo':
        #    msg = msg.copy(tempo=150000)
            frozen = freeze_message(msg)
            frozen_messages[i].append(frozen)

################

###ANALYZE FOR VELOCITY


for track in frozen_messages:
    for i, msg in enumerate(track):
        if  msg.type == 'note_on' or msg.type == 'note_off':
            gram = track[i:i+ORDER]
            nth = None
            nth_time = 0
            nth_onoff = '' #NONE
            if i+ORDER < len(track):
                nth = track[i+ORDER].bytes()
                nth_time = track[i+ORDER].time
                nth_onoff = track[i+ORDER].type
            else:
                #FIXME
                nth = track[i].bytes()
                nth_time = track[i].time
                nth_onoff = track[i].type

            bytes = [i.bytes() for i in gram if len(gram) >= ORDER]
            time = [i.time for i in gram if len(gram) >= ORDER]



            ##Byte_Notes
            byte_notes = [b[1] for b in bytes]
            byte_notes = tuple(byte_notes)



            if byte_notes not in note_map:
                note_map[byte_notes] = {nth[1]: (nth_onoff, nth_time)}
            else:
                for k,v in note_map[byte_notes].items():
                    if isinstance(k, int):
                        k = [k]+[nth[1]]
                        k = tuple(k)
                        #v = [v]
                        v = [v, (nth_onoff, nth_time)] ## BUG:
                        v = tuple(v)

                    else:

                        k = list(k)
                        k  = [*k, nth[1]]
                        k = tuple(k)
                        v = [*v, (nth_onoff, nth_time)]
                        v = tuple(v)
                    #v = list(v)

                    note_map[byte_notes] = {k:v}




'''
            ##Byte_Velocity
            byte_vel = [b[2] for b in bytes]
            byte_vel = tuple(byte_notes)

            if byte_vel not in vel_map:
                vel_map[byte_vel] = [nth[2]]
            else:
                vel_map[byte_vel] = vel_map[byte_vel] + [nth[2]]
'''
print('finished creating model')
##################

new_mid = MidiFile(type=1, ticks_per_beat=EIGHTH_NOTE_TICKS)

trigger_status = [{x+1 : 'off'} for x in range(127)]
#time_elapsed_between_notes_bool = False
err_count = 0

#PULSE
MEASURES = [] #[(starting measure number, (notes,in,order))]
for i,track in enumerate(frozen_messages):
    if i <= 0: #Variablecra

        ELAPSED_TICKS = 0

        CURRENT_MEASURE = [] #list of frozen mesages
        active_notes = 0

        octivator = [0,1,-1]
        octivator = octivator[i] * 12  #why not?

        new_track = MidiTrack()
        msg = mido.MetaMessage('set_tempo')
        msg = msg.copy(tempo=(BPM)) #VARIABLE
        new_track.append(msg)

        new_mid.tracks.append(new_track)

        starting_key = random.choice(list(note_map))


        key = starting_key
        print('starting key: ')
        print(key)
        print(QUANTIZATOIN)
        n = 0
        correct_notes = 4000
        while n < correct_notes:

            try:
                #All Data
                next_data = list(random.choice(list(note_map[key].items())))

                #Meta Data
                time_vel_status = random.choice(list(list(next_data)[1]))

                #Note Data

                #FIXME FOR SINGLE VALUES
                #print(next_data)
                #print(list(next_data)[0])
                next_note = None
                if isinstance(next_data[0], int):
                    next_note = next_data[0]
                else:
                    next_note = random.choice(list(next_data)[0])



                played_note = next_note
                if next_note + octivator > 126:
                    pass
                elif next_note + octivator < 1:
                    pass
                else:
                    played_note = next_note + octivator

                #Elapsed Time

                time_between_notes = None
                if isinstance(time_vel_status, int):

                    time_between_notes = time_vel_status
                else:

                    time_between_notes = time_vel_status[1]

                #QUANTIZE NOTES
            #    print(time_between_notes)
                for ind, dic in enumerate(QUANTIZATOIN):


                    v = list(dic.values())[0]
                #    print('time between notes: ' + str(time_between_notes) + f'{time_between_notes - v} is this less than 0')
                #    print(v)

                    if time_between_notes - v < 0:
                        if False:
                            time_between_notes = 0

                        else:
                            b = list(QUANTIZATOIN[ind].values())[0]
                            time_between_notes = b
                        break
            #    print(time_between_notes)
                    #lse:
                        #time_between_notes = list(QUANTIZATOIN[len(QUANTIZATOIN)-1].values())[0]
                        #print('big note')

                if time_between_notes > MAX_NOTE_LENGTH:
                    time_between_notes = MAX_NOTE_LENGTH
                #time_between_notes = time_vel_status[1]
                #FUCK   IT
                #scalar_sample = [1 for x in range (50)]
                #scalar_sample = scalar_sample + [2 for x in range(50)]

                #time_scalar = math.floor(time_between_notes * random.choice(scalar_sample)) + 1

                #time_between_notes = time_between_notes * time_scalar

                #Trigger Status
                onoff = None

                #Velocity
                soft_hit = [35+x for x in range(30)] #change ratios later

                medium_hit = [66+x for x in range(30)]

                hard_hit = [97+x for x in range(30)]

                vel = None
                for i in range(rhythmic%pulse):
                    if i % rhythmic == 0:
                        vel = [random.choice(hard_hit)]
                    elif i % (math.floor(rhythmic * 0.5)) == 0: #Math.floor
                        vel = vel + [random.choice(medium_hit)]
                    else:
                        vel = vel + [random.choice(soft_hit)]


                vel = vel[n%2]

                #MEAUSRE CONSTRUCTOR
                if ELAPSED_TICKS + time_between_notes % DOWN_BEAT_ON_ONE_X_MEASURES * BAR_LENGTH < time_between_notes + DOWN_BEAT_ON_ONE_X_MEASURES * BAR_LENGTH:
                    #shave off time to land on the downbeat
                    time_between_notes = time_between_notes - ELAPSED_TICKS + time_between_notes % DOWN_BEAT_ON_ONE_X_MEASURES * BAR_LENGTH

                    #add current measure to list
                    MEASURES.append((MEASURE_NUMBER, tuple(CURRENT_MEASURE)))

                    #clear the current measure
                    CURRENT_MEASURE = []

                    #DOWN_BEAT_ON_ONE_X_MEASURES * BAR_LENGTH has Elapsed
                    MEASURE_NUMBER = MEASURE_NUMBER + DOWN_BEAT_ON_ONE_X_MEASURES

                #Note is to be played immediately
                if time_between_notes < MIN_NOTE_LENGTH: #VARIABLE QUANTIZATOIN[5]['1/32'] QUANTIZATOIN[0]['1/384']


                    #print(next_note)
                    #print(trigger_status[next_note-1])
                    #If note is on, turn it off (same note in a row)
                    if trigger_status[next_note - 1][next_note] == 'on':
                        #Send a midi off message with NO delay
                        off_msg = mido.Message('note_off', note=played_note, velocity=vel , time=0)
                        new_track.append(off_msg)
                        ELAPSED_TICKS = ELAPSED_TICKS + 0
                        CURRENT_MEASURE.append(freeze_message(off_msg))


                    #LIMIT NUMBER OF NOTES TO BE PLAYED
                    off_notes = []
                    for x,y in enumerate(trigger_status):
                        if y[x+1] == 'on':
                            note = x+1 #note value
                            off_notes.append(note)

                    if len(off_notes) <= POLYPHONY:
                        #send immediately
                        on_msg = mido.Message('note_on', note=played_note, velocity=vel , time=0)
                        new_track.append(on_msg)
                        n = n + 1
                        ELAPSED_TICKS = ELAPSED_TICKS + 0
                        CURRENT_MEASURE.append(freeze_message(on_msg))

                        #ensure the note is recognized as on
                        trigger_status[next_note - 1][next_note] = 'on'
                    else:
                        on_msg = mido.Message('note_on', note=played_note, velocity=vel , time=MIN_NOTE_LENGTH)
                        new_track.append(on_msg)
                        n = n + 1
                        ELAPSED_TICKS = ELAPSED_TICKS + MIN_NOTE_LENGTH
                        CURRENT_MEASURE.append(freeze_message(on_msg))

                        #ensure the note is recognized as on
                        trigger_status[next_note - 1][next_note] = 'on'

                    #print(trigger_status[next_note-1])
                else:
                    #print(next_note)
                    #print(trigger_status[next_note-1])
                    #Turn off all sustain

                    #PT1: sustain off
                    off_notes = []
                    for x,y in enumerate(trigger_status):
                        if y[x+1] == 'on':
                            note = x+1 #note value
                            off_notes.append(note)
                    #PT 2: sustain off
                    for r,note in enumerate(off_notes):
                        if note + octivator > 126:
                            pass
                        elif note + octivator < 1:
                            pass
                        else:
                            pn = note + octivator
                        if r == 0:
                            #first off_note determines length of the sustained pitch(es)
                            nm = mido.Message('note_off', note=pn, velocity=vel , time=time_between_notes)
                            new_track.append(nm)
                            ELAPSED_TICKS = ELAPSED_TICKS + time_between_notes
                            #change the trigger STATUS
                            trigger_status[note-1][note] = 'off'
                            CURRENT_MEASURE.append(freeze_message(nm))
                        else:
                            nm = mido.Message('note_off', note=pn, velocity=vel , time=0)
                            new_track.append(nm)
                            ELAPSED_TICKS = ELAPSED_TICKS + 0
                            #change the trigger STATUS
                            trigger_status[note-1][note] = 'off'
                            CURRENT_MEASURE.append(freeze_message(nm))


                    #time = 0 so note plays immediately after sustain
                    on_msg = mido.Message('note_on', note=played_note, velocity=vel , time=0)
                    CURRENT_MEASURE.append(freeze_message(on_msg))
                    new_track.append(on_msg)
                    n = n+1
                    ELAPSED_TICKS = ELAPSED_TICKS + 0

                    #ensure the note is recognized as on
                    trigger_status[next_note - 1][next_note] = 'on'

                key = list(key)
                for j,k in enumerate(key):
                    if j + 1 < ORDER:
                        key[j] = key[j+1]
                    else:
                        key[j] = next_note
                key = tuple(key)

            except NameError as error:
                print(error)
                err_count = err_count + 1
                key = random.choice(list(note_map))

            except TypeError as error:
                err_count = err_count + 1
                print('got a type error for: ' + str(error))
                key = random.choice(list(note_map))

            except KeyError as error:
                err_count = err_count + 1
                print('got a key error for: ' + str(error))
                key = random.choice(list(note_map))

            except SystemError as error:
                err_count = err_count + 1
                print('error: ' + str(err_count))
                #Reset key
                key = random.choice(list(note_map))


                if err_count >= 1:
                    print(error)
                    #break




        for x,y in enumerate(trigger_status):
            new_message = mido.Message('note_off', note=x+1, velocity=0 , time=0)
            new_track.append(new_message)

new_mid.save('new_song.midi')


print('Error count: ' + str(err_count))
print(MEASURES)
for msg in new_mid.play():

    #print(msg)
    print(msg)
    port.send(msg)
print('Error count: ' + str(err_count))

if err_count >= 5000:
    print('Quit early')
