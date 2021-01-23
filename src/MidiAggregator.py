from src.MusicModel import MusicModel, AsyncMusicModel

from mido import MidiFile
from mido import Message, MidiFile, MidiTrack
import mido
import base64
import math
import time
import logging
import threading
import os

class Looper:
    def __init__(self):
        pass

class MidiAggregator:
    #output file is just the name the file is to be saved as || midi_file is the actual midifile object from Mido
    def __init__(self, ticks_per_beat=480, bpm=240, output_file='new_song.midi', backend='mido.backends.rtmidi', port='IAC Driver Bus 1'):
        self.backend = backend
        self.output_file = output_file
        mido.set_backend(backend)
        self.port_name = port
        self.port = mido.open_output(port)

        self.channel_ids = [{x:-1} for x in range(16)]
        self.channels = []

        self.midi_file = MidiFile(type=1, ticks_per_beat=ticks_per_beat) #beat set to eigth notes
        self.ticks_per_beat = ticks_per_beat
        self.quantization = [{f'1/{math.floor(8*x)}': math.floor(ticks_per_beat//x)} for x in [48,24,16,12,8,4,3,2,1.5,1,0.5,0.25,0.125]]
        self.bpm = mido.bpm2tempo(int(bpm))

    def add_channel(self, input_file, order=1, n=100, max_note_length=(12,'1/1'), min_note_length=(0,'1/384'), rhythm_grid=None):
        channel_number = self.retrieve_channel_id()

        if channel_number == -1:
            print('error adding channel...')
            return -1

        new_track = MidiTrack()

        #msg = mido.Message('control_change')
        #msg = msg.copy(channel=channel_number) #VARIABLE
        #new_track.append(msg)

        msg = mido.MetaMessage('set_tempo')
        msg = msg.copy(tempo=(self.bpm)) #VARIABLE
        new_track.append(msg)

        self.midi_file.tracks.append(new_track)



        #self.midi_file.tracks.append(new_track)

        channel = MusicModel.MusicModel(aggregator=self, order=order, input_file=input_file, output_file=self.output_file, midi_file=self.midi_file, n=n, channel_number=channel_number, max_note_length=max_note_length, min_note_length=min_note_length, max_measures=32, rhythm_grid=None)
        self.midi_file = channel.generate_midi_from_markov()
        self.channels.append(channel)

        return channel.rhythm_grid_out #rhythm of notes played -> bind this to future generated tracks?
        #print(channel_number)

    def retrieve_channel_id(self):
        for i,ids in enumerate(self.channel_ids):
            for k,v in ids.items():
                if v != 1 and int(k) == i:
                    self.channel_ids[i][k] = v * -1
                    return int(k)
        return -1

    def play(self):
        print(self.midi_file)
        for msg in self.midi_file.play():

            #print(msg)
            print(msg)
            self.port.send(msg)
        #print('Error count: ' + str(err_count))

class AsyncMidiAggregator(MidiAggregator): #FOR PLAYING BACK REAL TIME
    def __init__(self, ticks_per_beat=480, bpm=240, output_file='new_song.midi', backend='mido.backends.rtmidi', port='IAC Driver Bus 1'):
        super().__init__(ticks_per_beat=ticks_per_beat, bpm=bpm, output_file=output_file, backend=backend, port=port)
        self.threads = []
        self.files = []
        self.MAX_INPUTS = 16 #THIS IS A CONSTANT
        self.CURRENT_INPUTS = 0

    def add_channel(self, input_file, order=1, n=100, max_note_length=(12,'1/1'), min_note_length=(0,'1/384'), rhythm_grid=None):
        channel_number = self.retrieve_channel_id()

        if channel_number == -1:
            print('error adding channel...')
            return -1

        new_track = MidiTrack()

        msg = mido.MetaMessage('set_tempo')
        msg = msg.copy(tempo=(self.bpm)) #VARIABLE
        new_track.append(msg)

        self.midi_file.tracks.append(new_track)


        '''-----------------------------'''
        '''   USE THE AsyncMusicModel   '''
        '''-----------------------------'''

        #get the input files
        #input_file =

        channel = AsyncMusicModel(aggregator=self, order=order, input_file=input_file, output_file=self.output_file, midi_file=self.midi_file, n=n, channel_number=channel_number, max_note_length=max_note_length, min_note_length=min_note_length, max_measures=32, rhythm_grid=None)

        '''-----------------------------'''
        '''   CURRENTLY WONT RETURN     '''
        '''-----------------------------'''

        self.midi_file = channel.generate_inf_midi_from_markov()
        self.channels.append(channel)

        return channel.rhythm_grid_out #rhythm of notes played -> bind this to future generated tracks?

    def command_line_input(self):

        while self.CURRENT_INPUTS < self.MAX_INPUTS:
            file = input('What midi file do you want to use? (or DONE)\nfilename (inside midi folder): ')
            if file.upper() == 'DONE': break
            #Try
            mid = MidiFile(os.path.abspath(os.path.join('midi', file)))

            '''----------------------------------------------------------------------------------'''
            '''   If Multiple channels in the midi file, break apart into seperate files first   '''
            '''----------------------------------------------------------------------------------'''

            for i, track in enumerate(mid.tracks):
                if len(track) > 63: #SUFFICIENTLY LARGE FOR A MODEL

                    self.CURRENT_INPUTS += 1

                    temp_mid = MidiFile(type=1, ticks_per_beat=self.ticks_per_beat)
                    temp_track = MidiTrack()
                    t_msg = mido.MetaMessage('set_tempo')
                    t_msg = t_msg.copy(tempo=(self.bpm)) #VARIABLE
                    temp_track.append(t_msg)
                    temp_mid.tracks.append(temp_track)
                    for msg in track: #good number for a minimal markov chain
                        if msg.type != 'unknown_meta':
                            print(msg)
                            temp_track.append(msg)

                    new_file = os.path.abspath(os.path.join('src/tmp/async_split_midi', f'tmp_{file}_channel_{i}.midi'))
                    temp_mid.save(new_file)

                    self.files.append(new_file)



            #Except



if __name__ == '__main__':
    ma = AsyncMidiAggregator(bpm=70)

    ma.command_line_input()
    '''
    file = input('What midi file do you want to use? ')
    file2 = input('What midi file do you want to use? ')
    file3 = input('What midi file do you want to use? ')

    files = [file, file2, file3]

    '''
    for i, file in enumerate(ma.files):
        format = "%(asctime)s: %(message)s"
        logging.basicConfig(format=format, level=logging.INFO,
                            datefmt="%H:%M:%S")

        logging.info("Main    : before creating thread")

        channel_midi = threading.Thread(target=ma.add_channel, args=(file, 3))
        logging.info("Main    : before running thread")
        channel_midi.start()
        logging.info("Main    : wait for the thread to finish")
        # x.join()
        logging.info("Main    : all done")

    ##file3 = input('What midi file do you want to use? ')
    #file4 = input('What midi file do you want to use? ')
    #file2 = input('What midi file do you want to use? (2) ')
    #rhythm_grid = True
    #, min_note_length=(4,'1/64'))#, max_note_length=(4,'1/64'), min_note_length=(4,'1/64'))
    #ma.add_channel(input_file=file2, max_note_length=(11,'1/2'), min_note_length=(5,'1/32'),rhythm_grid=rhythm_grid) #MULTI THREAD THIS
    #ma.add_channel(input_file=file, max_note_length=(11,'1/2'), min_note_length=(11,'1/2'))
    #ma.add_channel(input_file=file3, max_note_length=(12,'1/1'), min_note_length=(12,'1/1'))
    #ma.add_channel(input_file=file, max_note_length=(5,'1/32'), min_note_length=(5,'1/32'))

    #ma.play()
    #for m in ma.channels
    #for m in ma.channels:
        #print(m.measure_number)
#    m = MusicModel.MusicModel(order=2, file=file)
#    print(m.model.get_time((62, 49)))
#    print(m)
#   new_mid = MidiFile(type=1, ticks_per_beat=480)
#    m.generate_midi_from_markov(n=4000, bpm=140, midi_file=new_mid)

#new_mid = MidiFile(type=1, ticks_per_beat=EIGHTH_NOTE_TICKS)

#trigger_status = [{x+1 : 'off'} for x in range(127)]
