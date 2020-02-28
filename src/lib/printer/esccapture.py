# -* coding: utf-8 *-
# (C) 2012 by Bernd Wurst <bernd@schokokeks.org>

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

import time
from .usbprinter import USBPrinter
from .esc import ESCPrinter

# Barcode chars
BARCODE_TXT_BLW = '\x1d\x48\x02' # HRI barcode chars below
BARCODE_FONT_A  = '\x1d\x66\x00' # Font type A for HRI barcode chars
BARCODE_HEIGHT  = '\x1d\x68\x64' # Barcode Height [1-255]
BARCODE_WIDTH   = '\x1d\x77\x03' # Barcode Width  [2-6]
BARCODE_EAN13   = '\x1d\x6b\x02' # Barcode type EAN13


 
class ESCCapture(ESCPrinter):
    def __init__(self, fileobject):
        self.printer_out = fileobject
        self.printer_in = None
        
    def __del__(self):
        pass
  
    def drawerIsOpen(self):
        return False

