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

# Barcode chars
BARCODE_TXT_BLW = '\x1d\x48\x02' # HRI barcode chars below
BARCODE_FONT_A  = '\x1d\x66\x00' # Font type A for HRI barcode chars
BARCODE_HEIGHT  = '\x1d\x68\x64' # Barcode Height [1-255]
BARCODE_WIDTH   = '\x1d\x77\x03' # Barcode Width  [2-6]
BARCODE_EAN13   = '\x1d\x6b\x02' # Barcode type EAN13



class ESCPrinter(object):
    def __init__(self):
        self.device = USBPrinter()
        if not self.device.initialized:
            raise RuntimeError()
        (self.printer_out, self.printer_in) = self.device.get_endpoints() 
        if not self.printer_out:
            raise RuntimeError('Cannot access printer!')
        self.reset()
        
    def __del__(self):
        del(self.device)
        
    def reset(self):
        # Reset printer
        self.printer_out.write(chr(27)+chr(64))
        # Set code page 858 (mit Euro-Zeichen)
        self.printer_out.write(chr(27)+chr(116)+chr(19))
        
    def encode(self, string):
        assert type(string) == str, 'illegal argument, cannot encode'
        return string.encode('cp858')


    def raw(self, command):
        self.printer_out.write(command)


    def ean13(self, code):
        if len(code) != 12:
            raise ValueError('require 12 digits')
        code = [int(i) for i in code]
        sum_ = lambda x, y: int(x) + int(y)
        evensum = reduce(sum_, code[::2])
        oddsum = reduce(sum_, code[1::2])
        check = (10 - ((evensum + oddsum * 3) % 10)) % 10
        code = ''.join([str(i) for i in code]) + str(check)
        # Align Bar Code()
        self.raw('\x1b\x61\x01') # center
        self.raw(BARCODE_HEIGHT)
        self.raw(BARCODE_WIDTH)
        self.raw(BARCODE_FONT_A)
        self.raw(BARCODE_TXT_BLW)
        self.raw(BARCODE_EAN13)
        # Print Code
        if code:
            self.raw(code)
        else:
            raise ValueError('No code')




    def text(self, string):
        self.printer_out.write(self.encode(string))

    def bold(self, state = True):
        if state:
            self.printer_out.write(chr(27)+chr(69)+chr(1))
        else:
            self.printer_out.write(chr(27)+chr(69)+chr(0))

    def underline(self, state = True):
        if state == 2:
            self.printer_out.write(chr(27)+chr(45)+chr(2))
        elif state == 1 or state == True:
            self.printer_out.write(chr(27)+chr(45)+chr(1))
        else:
            self.printer_out.write(chr(27)+chr(45)+chr(0))

    def align(self, align):
        command = 0
        if align == 'center':
            command = 1
        elif align == 'right':
            command = 2
        self.printer_out.write(chr(27)+chr(97)+chr(command))
    
    def font(self, type):
        command = 0
        if type == 'B':
            command = 1
        self.printer_out.write(chr(27) + chr(77) + chr(command))
        
    def fontsize(self, width, height):
        width = (width-1) % 8
        height = (height-1) % 8
        size = (width << 4) | height
        # set font scaling
        self.printer_out.write(chr(29)+chr(33)+chr( size ))
        # turn smoothing on
        self.printer_out.write(chr(29)+chr(98)+chr(1))        

    def cut(self, mode='full'):
        command = 0
        if mode == 'partial':
            command = 1
        blanklines = 3
        self.printer_out.write(chr(29)+chr(86)+chr(command+65) + chr(blanklines))

    def openDrawer(self):
        self.printer_out.write(chr(27)+chr(112)+chr(0)+chr(25)+chr(250))
  
    def drawerIsOpen(self):
        garbage = self.printer_in.read(32).tolist()
        assert len(garbage) < 32, 'Too much wasty data received from printer'
        self.printer_out.write(chr(27)+chr(117)+chr(0))
        status = None
        for i in range(100):
            time.sleep(0.01)
            recv = self.printer_in.read(32).tolist()
            if len(recv) > 0:
                status = recv[0]
                break
        if status & 0x01:
            return False 
        else:
            return True


if __name__ == '__main__':
    e = ESCPrinter()
    e.font('A')
    #e.reset()
    #rawdata = '\xff' * (16 * 32)
    #e.raw('\x1d\x76\x30\0\x02\0\x01\0\xff')
    #e.text('\n\n\n')
    e.fontsize(2,2)
    e.text('1234567890'*3)
    e.text('\n')
    e.ean13('200123456789')
    e.cut()
