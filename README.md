# pymusic
Pandora's Music Box
midi generation via markov chains (built on MacOS, verified with Logic X)

#preview of code running
[![Watch the video](https://www.teleradiopadrepio.it/wp-content/uploads/Youtube-Player-506.png)](https://youtu.be/3k6rQsKpXZU)


# downloading the code...
1. git clone
2. python -m venv .venv
3. source .venv/bin/activate (on MacOS)
4. pip install -r requirements.txt

#configuring the CPUs internal busses (MacOS)
*** mido.set_backend(backend) where backend == mido.backends.rtmidi by default (set in constructor) ***
https://mido.readthedocs.io/en/latest/message_types.html

- MacOs:
https://feelyoursound.com/setup-midi-os-x/
1. Launch the "Audio MIDI Setup" of macOS
2. Open the "Window" menu and click on "Show MIDI Studio"
3. Double-click on the IAC Driver icon
4. Activate the "Device is online" checkbox
5. You can rename the Device Name if you like, but please only use characters that are available on an English keyboard! "IAC Driver" is fine, "哈佬" not so much.
6. Create a new port by clicking on the "+" button below "Ports" (see the screenshot below). Again: Name the port as you like, but only use English characters (the second port name in the screenshot wouldn't show up in the feelyoursound.com software, for example).
7. Restart your DAW and your feelyoursound.com software
8. Set the MIDI Input of the DAW to the newly created MIDI port
9. Set the MIDI Output of the feelyoursound.com software to the newly created MIDI port as well

- Windows:
http://donyaquick.com/midi-on-windows/
2.3 Virtual MIDI Ports
A virtual MIDI port is a piece of software that runs in the background to send/receive MIDI messages from other programs or hardware devices. When running, virtual ports will show up in the Windows device manager under “sound, video, and game controllers. Virtual MIDI ports allow communication between MIDI-related programs that are not perceived by Windows as MIDI devices (which is to say that they do not show up in device manager). In other words, these programs might be able to send and receive MIDI messages, but they can’t “see” each other directly—but they will both be able to see a virtual MIDI port and can, therefore, use it to communicate. Hardware ports can be used similarly, although it often requires using a MIDI cable to create an ungainly self-loop (connecting a device’s output to its own input).

#running the code
1. python run.py
2. type: the_entertainer.midi (inside midi folder)
3. each additional filename creates a new midi channel (max 16)
*** BUG: currently playing all files under channel one... issue with mido? MusicModel.py line 492 track.append(msg) (could be issue with internal bus)***

4. type "DONE" to start
5. ctrl-c to stop async midi

#adjusting inputs
currently all inputs are hardcoded minus filenames

- channel_midi = threading.Thread(target=ma.add_channel, args=(file, 3))
- adjust args=(file, <number>) where number is the ngram length, and file is the associated filename
- currently it applies the same ngram length to all files.
- other values (max/min note length, bpm, are also hardcoded) and need to be adjusted based on the construction of the input midifile

#dependencies
- (not used) fluidsynth==0.2
- (not used) future==0.18.2
- (unsure) midi2audio==0.1.1
- (important) mido==1.2.0   <- makes midi friendlier
- (unsure) pyFluidSynth==1.2.5
- (important) python-rtmidi==1.4.5  <- this is the midi bus manager
  https://spotlightkid.github.io/python-rtmidi/

#adding dependencies
- pip freeze > requirements.txt
