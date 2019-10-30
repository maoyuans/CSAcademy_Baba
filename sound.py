import json
import requests
import io
from pygame import mixer
from threading import Timer, Lock

class Sound(object):
    def __init__(self, file):
        mixer.init()
        mixer.music.load(file)
        self.playing = False
        self.currentPos = 0
        self.loop = False
        self._quit = False
        self.musicLock = Lock()
        Timer(0.1, self.checkDone).start()

    def play(self, doLoop=False, doRestart=False):
        with self.musicLock:
            if self.playing and not doRestart: return
            self.playing = True
            self.loop = doLoop
            if doRestart: self.currentPos = 0
            mixer.music.play(start=self.currentPos)

    def pause(self):
        with self.musicLock:
            if not self.playing: return
            self.playing = False
            self.currentPos += (mixer.music.get_pos() / 1000)
            mixer.music.pause()

    def checkDone(self):
        with self.musicLock:
            if mixer.music.get_pos() == -1:
                self.playing = False
                self.currentPos = 0
                if self.loop:
                    mixer.music.play()

        Timer(0.1, self.checkDone).start()

import os
import sys

def main():
    soundUrl = json.loads(sys.stdin.readline())['url']

    r = requests.get(soundUrl, stream=True)
    s = Sound(io.BytesIO(r.content))

    while True:
        request = json.loads(input())
        command = request['command']
        kwargs = request['kwargs']
        commandMap = {'pause': s.pause, 'play': s.play}
        commandMap[command](**kwargs)

if __name__ == "__main__":
    main()
