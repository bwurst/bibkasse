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

from PyQt5 import QtWidgets, uic
import sys
import os
import cups

from lib.Config import config

class WidgetBeleg(QtWidgets.QWidget):
    def __init__(self, mainwindow):
        QtWidgets.QWidget.__init__(self)
        self.mainwindow = mainwindow
        
        try:
            self.ui = uic.loadUi('ressource/ui/widget_beleg.ui', self)
        except:
            print ('Kann UI-Datei nicht laden!')
            sys.exit(1)  

        self.connectSlots()


    def update(self):
        pass

        
    def showBeleg(self, filename):
        self.aktueller_beleg = filename
        self.mainwindow.kundendisplay.showBeleg(self.aktueller_beleg)
        with open(filename.replace('.pdf', '.html'), mode='r', encoding='utf-8') as f:
            text = f.read()
            self.ui.textBrowser_beleg.setHtml(text)
        self.ui.textBrowser_beleg.setStyleSheet('''
        * {
          font-size: 11pt;
        }
        ''')

    def bondrucken(self):
        self.mainwindow.kundendisplay.drucken()
        
    def qrcode(self):
        self.mainwindow.kundendisplay.qrcode()
        
    def rechnung(self):
        c = cups.Connection()
        c.printFile(c.getDefault(), self.aktueller_beleg, os.path.basename(self.aktueller_beleg), config('printer_plain'))
        

    def connectSlots(self):
        self.ui.button_zurueck.clicked.connect(self.mainwindow.showStartpage)
        self.ui.button_bon.clicked.connect(self.bondrucken)
        self.ui.button_rechnung.clicked.connect(self.rechnung)
        self.ui.button_qrcode.clicked.connect(self.qrcode)
       
    
