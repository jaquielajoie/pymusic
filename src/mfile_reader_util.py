from mido import MidiFile
from mido import Message, MidiFile, MidiTrack
import mido
import pygame
import base64
import math
import time
import logging
import threading

mido.set_backend('mido.backends.rtmidi')
port = mido.open_output('IAC Driver Bus 1')

file = input('midi file: ')
mid = MidiFile('../'+file)
#current_track = None



'''
def thread_function(name):
    logging.info("Thread %s: starting", name)
    time.sleep(2)
    logging.info("Thread %s: finishing", name)
'''

def print_play(name, track):
    logging.info("Thread %s: starting", name)

    for msg in track:
        #time.sleep(msg.time)
        time.sleep(int((msg.time + name) /240))# / 480)) #480 is the default ticks per 8th note
        if msg.type != 'unknown_meta':
            print(msg)
            if not msg.is_meta:
                port.send(msg)
        elif hasattr(msg, 'data'):
            print('\nUnknown meta message type: ' + str(msg.type_byte) + '\nmsg data: ' + str(msg.data))
        else:
            print('\nUnknown meta message type: ' + str(msg.type_byte) + '\nNo data associated with unknown meta message')
        #if not msg.is_meta:
            #port.send(msg)
    logging.info("Thread %s: finishing", name)

if __name__ == "__main__":




    for i, track in enumerate(mid.tracks):
        print('Track {}: {}'.format(i, track.name))

        format = "%(asctime)s: %(message)s"
        logging.basicConfig(format=format, level=logging.INFO,
                            datefmt="%H:%M:%S")

        current_track = track
        logging.info("Main    : before creating thread")

        channel_midi = threading.Thread(target=print_play, args=(i,track))
        logging.info("Main    : before running thread")
        channel_midi.start()
        logging.info("Main    : wait for the thread to finish")
        # x.join()
        logging.info("Main    : all done")
