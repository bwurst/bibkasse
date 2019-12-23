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

from lib.Speicher import Speicher

import subprocess, os, sys, time

def shutdown():
    subprocess.call(['dbus-send', '--system', '--print-reply',
                     '--dest=org.freedesktop.ConsoleKit', 
                     '/org/freedesktop/ConsoleKit/Manager', 
                     'org.freedesktop.ConsoleKit.Manager.Stop']
                     )
    
def restart(main):
    speicher = Speicher()
    speicher.lock()
    speicher.unmount()
    
    try:
        main.printer.terminate()
    except:
        pass
    sys.exit(99)