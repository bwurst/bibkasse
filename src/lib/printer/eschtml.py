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

 
class ESCHTML(ESCPrinter):
    def __init__(self, fileobject):
        self.printer_out = fileobject
        self.printer_in = None
        self.printer_out.write('''<html><head><style>
p {
    margin: 0;
    padding: 0;
}
body {
    font-family: monospace;
    width: 48ex;
    padding: 2em;
    border: 1px solid black;
}
</style></head><body>''')
        self.open_tags = ['html', 'body']
        self._open_p = False
        self._fontsize = (1,1)
        self._align = 'left'
        self._bold = False
        self._underlined = False

    def reset(self):
        pass

    def text(self, string):
        for line in string.splitlines(keepends=True):
            self.p(line)
            

    def bold(self, state=True):
        self._bold = state
        self._formatchanged = True


    def underline(self, state=True):
        self._underlined = state
        self._formatchanged = True


    def align(self, align):
        self._align = align
        self._formatchanged = True


    def font(self, type):
        pass


    def fontsize(self, width, height):
        self._fontsize = (width, height)
        self._formatchanged = True

    def p(self, text):
        style = []
        if self._bold:
            style.append('font-weight: bold;')
        if self._underlined:
            style.append('text-decoration: underline;')
        if self._fontsize in [(2,2), (1,2)]:
            style.append('font-size: 200%;')
        if self._fontsize == (1,2):
            style.append('font-stretch: 50%;')             
        if self._fontsize == (2,1):
            style.append('font-stretch: 200%;')             
        
        if not self._open_p:
            self.printer_out.write('<p style="text-align: %s;">' % (self._align))
            self._open_p = True 
        if text == '\n':
            text = '&nbsp;\n'
        text = text.replace('  ', ' &nbsp;')
        self.printer_out.write('<span style="%s">%s</span>' % (' '.join(style), text.replace('\n', ''),))
        if text.endswith('\n'):
            self.printer_out.write('</p>\n')
            self._open_p = False


    def cut(self):
        for tag in reversed(self.open_tags):
            self.printer_out.write('</%s>' % tag)

        
    def __del__(self):
        pass
  
    
  
    def drawerIsOpen(self):
        return False

