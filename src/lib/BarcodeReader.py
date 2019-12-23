# -* coding: utf-8 *-
# (C) 2011 by Bernd Wurst <bernd@schokokeks.org>

# This file is part of Bib2011.
#
# Bib2011 is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Bib2011 is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Bib2011.  If not, see <http://www.gnu.org/licenses/>.

import select, subprocess, os, time
import threading

from Beep import beep

ZBARCAM = '/usr/bin/zbarcam'

class BarcodeReader(threading.Thread):
    def __init__(self):
        if not os.path.exists(ZBARCAM):
            raise RuntimeError('zbarcam not found. zbar-tools not installed?')
        threading.Thread.__init__(self)
        self.daemon = True
        self.__exit = False
        self.__result = None
        subprocess.call('killall zbarcam', shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        
    
    def run(self):
        __poll = select.poll()
        lastone = ''
        while not self.__exit:
            zbar = subprocess.Popen([ZBARCAM, '--nodisplay'], stdout = subprocess.PIPE, stderr = subprocess.PIPE, shell=False)
            __poll.register(zbar.stdout)
            while zbar.poll() == None:
                events = __poll.poll(0.5)
                if events == []:
                    # timeout
                    if self.__exit:
                        zbar.kill()
                        break
                    continue
                lastone = zbar.stdout.readline().strip()
                if lastone.startswith('EAN-13:2'):
                    self.found(lastone[7:])
            __poll.unregister(zbar.stdout)


    def found(self, code):
        beep()
        print ('found: %s' % code)
        self.__result = (time.time(), code)

    def get(self):
        if not self.__result:
            return None
        t, code = self.__result
        if t > (time.time() - 3):
            self.__result = None
            return code
        else:
            return None

    def terminate(self):
        self.__exit = True
        if self.isAlive():
            self.join()


if __name__ == '__main__':
    bc = BarcodeReader()
    bc.start()
    while True:
        code = bc.get()
        time.sleep(0.1)
        if code:
            print (code)
            break
    bc.terminate()
