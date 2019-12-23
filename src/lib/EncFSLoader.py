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

import sys, os, subprocess


class EncFSLoader(object):
    def __init__(self):
        self.mounted = False
        self.we_mounted = False
        
    def get_backend_path(self):
        return os.path.join(os.path.realpath(os.path.dirname(self.path)),
                            'encfs_'+os.path.basename(self.path))
        
    def mount(self, path, passphrase):
        self.path = os.path.realpath(path)
        if os.path.ismount(self.path):
            print ('already mounted!')
            self.mounted = True
            return
        if not os.path.exists(self.get_backend_path()):
            raise ValueError("EncFS ist noch nicht eingerichtet! Das muss manuell gemacht werden.")
        if not os.path.exists(self.path):
            print ("Erstelle Datenbank-Verzeichnis")
            os.mkdir(self.path)
        print ('mounting')
        proc = subprocess.Popen(['encfs', '-S', self.get_backend_path(), self.path], stdin=subprocess.PIPE)
        proc.stdin.write(passphrase+b'\n')
        proc.stdin.close()
        if proc.wait() == 0:
            self.mounted = True
            self.we_mounted = True
        

    def unmount(self):
        if self.we_mounted:
            print ('unmounting %s' % self.path)
            subprocess.call(['fusermount', '-zu', self.path])
            self.mounted = False
        else:
            print ('not unmounting (was not mounted)')