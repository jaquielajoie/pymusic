
#folder.filename
from src.MidiAggregator import AsyncMidiAggregator
import time
import logging
import threading

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
