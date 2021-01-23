from mido import MidiFile
import mido
from mido import Message
from mido.frozen import freeze_message, thaw_message
from mido.frozen import FrozenMessage
from mido import Message, MidiFile, MidiTrack
import math
import random
import time

class MusicModel:
    def __init__(self, aggregator, channel_number, midi_file, output_file, input_file='', order=5, n=100, max_note_length=(12,'1/1'), min_note_length=(0,'1/384'), max_measures=96, rhythm_grid=None):
        self.midi_file = midi_file
        self.output_file = output_file
        self.channel_number = channel_number
        self.input_file = input_file
        self.n = n #number of notes to generate
        self.order = order
        self.model = self.create_markov_model()
        self.aggregator = aggregator
        self.quantization = [{f'1/{math.floor(8*x)}': math.floor(self.aggregator.ticks_per_beat//x)} for x in [48,24,16,12,8,4,3,2,1.5,1,0.5,0.25,0.125]]
        self.max_note_length = self.quantization[max_note_length[0]][max_note_length[1]]
        self.min_note_length = self.quantization[min_note_length[0]][min_note_length[1]]
        self.pulse = 32
        self.rhythmic = 7
        self.beat_value = self.aggregator.ticks_per_beat
        self.bar_length = 4  * self.beat_value
        self.measure_number = 1
        self.down_beat_on_one_x_measures = 8
        self.measures = []
        self.polyphony = 3
        self.max_measures = max_measures
        self.current_measure_ticks = 0
        self.rhythm_grid = rhythm_grid
        self.rhythm_grid_out = None


    def __str__(self):
        str('This is MusicModel on channel #: ' + self.channel_number)
        return ''

    def create_markov_model(self):

        note_map_on = NoteMap()
        note_map_off = NoteMap()
        trigger_sequence = TriggerMap()
        note_map_complete = NoteMap()

        if self.input_file == '':
            #print('error, no file supplied for channel ' + str(self.channel))
            return note_maps

        mid = MidiFile(self.input_file)



        frozen_messages = []
        for i, track in enumerate(mid.tracks):
            ##print('Track {}: {}'.format(i, track.name))
            frozen_messages.append([])
            for msg in track:
                frozen_messages[i].append(freeze_message(msg))

        ##print(frozen_messages)
        for track in frozen_messages:
            ##print(len(frozen_messages))
            for i, msg in enumerate(track):
                if  msg.type == 'note_on' or msg.type == 'note_off':
                    ##print(msg)
                    gram = track[i:i+self.order]
                    nth = None
                    nth_time = 0
                    nth_onoff = '' #NONE
                    if i+self.order < len(track):
                        nth = track[i+self.order].bytes()
                        nth_time = track[i+self.order].time
                        nth_onoff = track[i+self.order].type
                    else:
                        #FIXME
                        nth = track[i].bytes()
                        nth_time = track[i].time
                        nth_onoff = track[i].type

                    bytes = [i.bytes() for i in gram if len(gram) >= self.order]
                    time = [i.time for i in gram if len(gram) >= self.order]
                    triggers = [i.type for i in gram if len(gram) >= self.order]

                    ##Byte_Notes
                    byte_notes = [b[1] for b in bytes]
                    byte_notes = tuple(byte_notes)

                    trigger_key = tuple(triggers)

                    if nth_onoff == 'note_on':
                        note_map_on.add_note(outer_key=byte_notes, nth_note=nth[1], nth_onoff=nth_onoff, nth_time=nth_time)
                        note_map_complete.add_note(outer_key=byte_notes, nth_note=nth[1], nth_onoff=nth_onoff, nth_time=nth_time)
                    elif nth_onoff == 'note_off':
                        note_map_off.add_note(outer_key=byte_notes, nth_note=nth[1], nth_onoff=nth_onoff, nth_time=nth_time)
                        note_map_complete.add_note(outer_key=byte_notes, nth_note=nth[1], nth_onoff=nth_onoff, nth_time=nth_time)

                    trigger_sequence.add_note(outer_key=trigger_key,nth_onoff=nth_onoff)

        return (note_map_on, note_map_off, trigger_sequence, note_map_complete)

    def generate_midi_from_markov(self):
        #key = self.model.random_key()
        err_count = 0
        #quit()
        ##print(self.model)
        #trigger_status = [] #[{x+1 : 'off'} for x in range(127)]
        #model_note_on = self.model[0]
        ##print(model_note_on)
        #model_note_off = self.model[1]
        model_trigger = self.model[2]
        model_complete = self.model[3]

        trigger_key = model_trigger.random_key()
        #on_key = model_note_on.random_key() #FIXME
        #off_key = model_note_off.random_key() #FIXME
        key = model_complete.random_key()
        rhythm_grid_out = []

        for tr, track in enumerate(self.midi_file.tracks):
            ##print('------')
            n = 0
            correct_notes = self.n
            elapsed_ticks = 0

            active_note_count = 0
            active_notes = []

            current_measure = []
            measure_number = self.measure_number
            zero_notes = 0

            while self.measure_number <= self.max_measures and tr == self.channel_number: #divide by polyphony for???
                ##print('...trying....')
                try:

                    #model_note_on = self.model[0]
                    #model_note_off = self.model[1]

                    ##print('here 1')
                    onoff = model_trigger.get_data(trigger_key)
                    ##print(model_trigger)
                    ##print(onoff)
                    #onoff_i = None
                    #key = None

                    trigger_key = list(trigger_key)

                    for j,k in enumerate(trigger_key):
                        if j + 1 < self.order:
                            trigger_key[j] = trigger_key[j+1]
                        else:
                            trigger_key[j] = onoff

                    trigger_key = tuple(trigger_key)

                    #key = complete_key
                    '''
                    if onoff == 'note_on' and active_note_count < self.polyphony:
                        #onoff_i = 0
                        #key = on_key
                        active_note_count = active_note_count + 1

                    elif onoff == 'note_off' and active_note_count > 0:
                        #onoff_i = 1
                        #key = off_key
                        active_note_count = active_note_count - 1

                    else:
                        quit()
                    '''
                    #else:
                        #trigger_key = model_trigger.random_key()
                        #on_key = model_note_on.random_key()
                        #off_key = model_note_off.random_key()
                        #active_note_count = 0
                        ##print('...else....')
                        #continue

                    model_note = self.model[3] #onoff_i

                    next_data = model_note.get_data(key, self.quantization) #(NOTE, TIME)
                    #print(next_data)
                    #continue
                    next_note = next_data[0]
                    next_time = next_data[1]


                    played_note = next_note

                    soft_hit = [35+x for x in range(30)]

                    medium_hit = [66+x for x in range(30)]

                    hard_hit = [97+x for x in range(30)]

                    vel = None
                    for i in range(self.rhythmic%self.pulse):
                        if i % self.rhythmic == 0:
                            vel = [random.choice(hard_hit)]
                        elif i % (math.floor(self.rhythmic * 0.5)) == 0: #Math.floor
                            vel = vel + [random.choice(medium_hit)]
                        else:
                            vel = vel + [random.choice(soft_hit)]


                    vel = vel[self.n%2]

                    on_off = None
                    if next_time >= self.max_note_length:
                        next_time = self.max_note_length
                        zero_notes = 0
                        #on_off = 'note_off'
                    elif next_time <= self.min_note_length and next_time != 0:
                        next_time = self.min_note_length
                        zero_notes = 0
                        #on_off = 'note_off'
                    elif next_time == 0:
                        #next_time = self.min_note_length

                        '''
                        FIXME ZERO NOTES
                        '''
                        zero_notes = zero_notes + 1
                        if zero_notes > self.polyphony:
                            next_time = self.min_note_length
                            zero_notes = 0


                        pass

                    elapsed_ticks = elapsed_ticks + next_time

                    allow_ties = None
                    if elapsed_ticks >= self.bar_length:
                        elapsed_ticks = elapsed_ticks - self.bar_length
                        self.measure_number = self.measure_number + 1
                        if self.measure_number % self.down_beat_on_one_x_measures == 0:
                            allow_ties = False
                        else:
                            allow_ties = True
                        if not allow_ties:
                            next_time = next_time - elapsed_ticks
                            elapsed_ticks = 0

                    elif elapsed_ticks == self.bar_length:
                        elapsed_ticks = 0
                        self.measure_number = self.measure_number + 1

                    '''
                    FORMAT TO GRID IF PRESENT
                    '''

                    if self.rhythm_grid != None:
                        if elapsed_ticks not in self.rhythm_grid:
                            continue #FIX THIS
                            '''
                            THIS CAN BE IMPROVED?
                            '''


                    ##print(self.measure_number)
                    #trigger_status.append((next_note, 0))

                    #CREATE MESSAGES

                    if next_note in active_notes:
                        onoff = 'note_off'
                    else:
                        onoff = 'note_on'
                    active_notes.remove(next_note) if onoff == 'note_off' else active_notes.append(next_note)

                    if active_note_count < self.polyphony:
                        #Can create a new on msg
                        msg = mido.Message(onoff, note=next_note, velocity=vel,channel=self.channel_number , time=next_time)

                    elif active_note_count > 0:
                        #Too many notes, remove some
                        onoff = 'note_off'
                        msg = mido.Message(onoff, note=next_note, velocity=vel,channel=self.channel_number , time=next_time)
                        #msg = mido.Message(onoff, note=next_note, velocity=vel,channel=self.channel_number , time=next_time)
                    else:
                        print('error in music model logic')
                        quit()

                    if onoff == 'note_on':
                        active_note_count += 1
                    else:
                        active_note_count -= 1

                    track.append(msg)
                    print(f'CHANNEL: {self.channel_number}\n\t{onoff}-------{next_note}----{self.measure_number}-----{elapsed_ticks}----{next_time}-----{elapsed_ticks}/{self.bar_length}---')
                    rhythm_grid_out.append(elapsed_ticks)


                    key = list(key) #model_note.random_key())
                    for j,k in enumerate(key):
                        if j + 1 < self.order:
                            key[j] = key[j+1]
                        else:
                            key[j] = next_note
                    key = tuple(key)

#                except KeyError as error:
#                    err_count = err_count + 1
#                    #print('got a key error for: ' + str(error))
#                    #print(str(self.channel_number) + ' ' + str(self.measure_number) + ' measure number')
#                    key = self.model.random_key()

                except TypeError as error:
                    err_count = err_count + 1
                    #print(error)
                    #throw(error)
                    #Reset key
                    key = self.model.random_key()

                    if err_count >= 1:
                        #print(error)
                        break

                except SystemError as error:
                    err_count = err_count + 1
                    #print('error: ' + str(err_count))
                    #Reset key
                    key = self.model.random_key()

                    if err_count >= 1:
                        #print(error)
                        break

            for x,y in enumerate(range(127)):
                new_message = mido.Message('note_off', note=x+1, velocity=0,channel=self.channel_number , time=0)
                track.append(new_message)
        self.rhythm_grid_out = rhythm_grid_out
        self.midi_file.save(self.output_file)
        return self.midi_file #THIS MUST BE THE RETURN


class AsyncMusicModel(MusicModel):
    def __init__(self, aggregator, channel_number, midi_file, output_file, input_file='', order=5, n=100, max_note_length=(12,'1/1'), min_note_length=(0,'1/384'), max_measures=96, rhythm_grid=None):
        super().__init__(aggregator=aggregator, channel_number=channel_number, midi_file=midi_file, output_file=output_file, input_file=input_file, order=order, n=n, max_note_length=max_note_length, min_note_length=min_note_length, max_measures=max_measures, rhythm_grid=rhythm_grid)
        self.playing = True

    def generate_inf_midi_from_markov(self):
        err_count = 0
        model_trigger = self.model[2]
        model_complete = self.model[3]
        trigger_key = model_trigger.random_key()
        key = model_complete.random_key()
        rhythm_grid_out = []

        for tr, track in enumerate(self.midi_file.tracks):
            ##print('------')
            n = 0
            correct_notes = self.n
            elapsed_ticks = 0

            active_note_count = 0
            active_notes = []

            current_measure = []
            measure_number = self.measure_number
            zero_notes = 0

            while self.playing:
                ##print('...trying....')
                try:
                    onoff = model_trigger.get_data(trigger_key)
                    trigger_key = list(trigger_key)

                    for j,k in enumerate(trigger_key):
                        if j + 1 < self.order:
                            trigger_key[j] = trigger_key[j+1]
                        else:
                            trigger_key[j] = onoff

                    trigger_key = tuple(trigger_key)

                    model_note = self.model[3] #onoff_i

                    next_data = model_note.get_data(key, self.quantization) #(NOTE, TIME)

                    next_note = next_data[0]
                    next_time = next_data[1]
                    played_note = next_note

                    soft_hit = [35+x for x in range(30)]

                    medium_hit = [66+x for x in range(30)]

                    hard_hit = [97+x for x in range(30)]

                    vel = None
                    for i in range(self.rhythmic%self.pulse):
                        if i % self.rhythmic == 0:
                            vel = [random.choice(hard_hit)]
                        elif i % (math.floor(self.rhythmic * 0.5)) == 0: #Math.floor
                            vel = vel + [random.choice(medium_hit)]
                        else:
                            vel = vel + [random.choice(soft_hit)]


                    vel = vel[self.n%2]
                    vel = 93

                    on_off = None
                    if next_time >= self.max_note_length:
                        next_time = self.max_note_length
                        zero_notes = 0
                        #on_off = 'note_off'
                    elif next_time <= self.min_note_length and next_time != 0:
                        next_time = self.min_note_length
                        zero_notes = 0
                        #on_off = 'note_off'
                    elif next_time == 0:
                        #next_time = self.min_note_length

                        '''
                        FIXME ZERO NOTES
                        '''
                        zero_notes = zero_notes + 1
                        if zero_notes > self.polyphony:
                            next_time = self.min_note_length
                            zero_notes = 0


                        pass

                    elapsed_ticks = elapsed_ticks + next_time

                    allow_ties = None
                    if elapsed_ticks >= self.bar_length:
                        elapsed_ticks = elapsed_ticks - self.bar_length
                        self.measure_number = self.measure_number + 1
                        if self.measure_number % self.down_beat_on_one_x_measures == 0:
                            allow_ties = False
                        else:
                            allow_ties = True
                        if not allow_ties:
                            next_time = next_time - elapsed_ticks
                            elapsed_ticks = 0

                    elif elapsed_ticks == self.bar_length:
                        elapsed_ticks = 0
                        self.measure_number = self.measure_number + 1

                    '''
                    FORMAT TO GRID IF PRESENT
                    '''

                    if self.rhythm_grid != None:
                        if elapsed_ticks not in self.rhythm_grid:
                            continue #FIX THIS
                            '''
                            THIS CAN BE IMPROVED?
                            '''


                    ##print(self.measure_number)
                    #trigger_status.append((next_note, 0))

                    #CREATE MESSAGES

                    if next_note in active_notes:
                        onoff = 'note_off'
                    else:
                        onoff = 'note_on'
                    active_notes.remove(next_note) if onoff == 'note_off' else active_notes.append(next_note)

                    if active_note_count < self.polyphony:
                        #Can create a new on msg
                        msg = mido.Message(onoff, note=next_note, velocity=vel,channel=self.channel_number , time=next_time)

                    elif active_note_count > 0:
                        #Too many notes, remove some
                        onoff = 'note_off'
                        msg = mido.Message(onoff, note=next_note, velocity=vel,channel=self.channel_number , time=next_time)
                        #msg = mido.Message(onoff, note=next_note, velocity=vel,channel=self.channel_number , time=next_time)
                    else:
                        print('error in music model logic')
                        quit()

                    if onoff == 'note_on':
                        active_note_count += 1
                    else:
                        active_note_count -= 1

                    track.append(msg)

                    """-------------------------------------------"""
                    """    This is where the thread sends midi    """
                    """-------------------------------------------"""

                    sleep_time =  (next_time/self.bar_length) * 2
                    time.sleep(sleep_time)
                    self.aggregator.port.send(msg)
                    print(f'CHANNEL: {self.channel_number}\n\t{onoff}-------{next_note}----{self.measure_number}-----{elapsed_ticks}----{next_time}-----{elapsed_ticks}/{self.bar_length}---')
                    rhythm_grid_out.append(elapsed_ticks)


                    key = list(key) #model_note.random_key())
                    for j,k in enumerate(key):
                        if j + 1 < self.order:
                            key[j] = key[j+1]
                        else:
                            key[j] = next_note
                    key = tuple(key)

#                except KeyError as error:
#                    err_count = err_count + 1
#                    #print('got a key error for: ' + str(error))
#                    #print(str(self.channel_number) + ' ' + str(self.measure_number) + ' measure number')
#                    key = self.model.random_key()

                except TypeError as error:
                    err_count = err_count + 1
                    #print(error)
                    #throw(error)
                    #Reset key
                    key = self.model.random_key()

                    if err_count >= 1:
                        #print(error)
                        break

                except SystemError as error:
                    err_count = err_count + 1
                    #print('error: ' + str(err_count))
                    #Reset key
                    key = self.model.random_key()

                    if err_count >= 1:
                        #print(error)
                        break

            for x,y in enumerate(range(127)):
                new_message = mido.Message('note_off', note=x+1, velocity=0,channel=self.channel_number , time=0)
                track.append(new_message)

        self.rhythm_grid_out = rhythm_grid_out
        self.midi_file.save(self.output_file)
        return self.midi_file #THIS MUST BE THE RETURN


class TriggerMap:
    def __init__(self):
        self.map = {}
    def add_note(self, outer_key, nth_onoff):
        if outer_key not in self.map:
            self.map[outer_key] = nth_onoff
        else:
            v = self.map[outer_key]
            #for v in self.map[outer_key]:
            if isinstance(v, str):
                v = [v] + [nth_onoff]
                v = tuple(v)
            else:
                v = list(v)
                v = [*v, nth_onoff]
                v = tuple(v)

            self.map[outer_key] = v
    def get_data(self,outer_key): #FIXME
        next_data = None
        if outer_key in self.map:
            next_data = random.choice(list(self.map[outer_key]))
        else:
            while outer_key not in self.map:
                outer_key = self.random_key()
            next_data = random.choice(list(self.map[outer_key]))

        #print(next_data)

        if next_data == 'note_on' or next_data == 'note_off':
            return next_data
        else:
            while next_data not in ['note_on','note_off']:
                next_data = random.choice(list(self.map[self.random_key()]))
                #print(next_data)
            return next_data

    def random_key(self):
        rand = random.choice(list(self.map))
        ##print(rand)
        return rand

class NoteMap:
    def __init__(self):
        self.map = {} #k:v //

    def __str__(self):
        #print("\n ngrams in model: \n")
        kvals = 0
        for k,v in self.map.items():
            #print("{} (next note(s): {}) ".format(k, list(v.keys())[0]))
            kvals = kvals + 1
        return '\n Done #printing NoteMap, ' + str(kvals) + ' ngram choices \n'

    def add_note(self, outer_key, nth_note, nth_onoff, nth_time):
        if outer_key not in self.map:
            self.map[outer_key] = {nth_note: (nth_onoff, nth_time)}
        else:
            for k,v in self.map[outer_key].items():
                if isinstance(k, int):
                    k = [k]+[nth_note]
                    k = tuple(k)
                    v = [v, (nth_onoff, nth_time)] ## BUG:
                    v = tuple(v)
                else:
                    k = list(k)
                    k  = [*k, nth_note]
                    k = tuple(k)
                    v = [*v, (nth_onoff, nth_time)]
                    v = tuple(v)

                self.map[outer_key] = {k:v}

    def get_data(self, outer_key, quantization=None): #gets note value and time value
        next_data = None
        if outer_key in self.map:
            next_data = list(random.choice(list(self.map[outer_key].items())))
        else:
            while outer_key not in self.map:
                outer_key = self.random_key()

            next_data = list(random.choice(list(self.map[outer_key].items())))

        next_note = None
        next_time = None
        if isinstance(next_data[0], int):
            next_note = next_data[0]
            next_time = next_data[1][1]
            ##print('A')
            ##print(next_data)
        else:
            next_note = random.choice(list(next_data)[0])
            next_time = random.choice(list(next_data[1]))[1]
            ##print('B')
            ##print(next_data)

        if quantization is not None:
            for ind, dic in enumerate(quantization):

                v = list(dic.values())[0]
                if next_time == 0:
                    break
                elif next_time - v <= 0:
                        next_time = list(quantization[ind].values())[0]
                        break

        return (next_note, next_time)

    def random_key(self):
        return random.choice(list(self.map))

if __name__ == '__main__':
    input_file = input('What midi file do you want to use? ')
    m = MusicModel(order=2, input_file=input_file)
    ##print(m.model.get_time((62, 49)))
    ##print(m)
    new_mid = MidiFile(type=1, ticks_per_beat=480)
    m.generate_midi_from_markov(n=4000, bpm=150000, midi_file=new_mid)

'''
    def get_time(self, outer_key):

        next_data = list(random.choice(list(self.map[outer_key].items())))
        time_vel_status = random.choice(list(list(next_data)[1]))

        time_between_notes = None
        if isinstance(time_vel_status, int):

            time_between_notes = time_vel_status
        else:

            time_between_notes = time_vel_status[1]

        return time_between_notes
'''
