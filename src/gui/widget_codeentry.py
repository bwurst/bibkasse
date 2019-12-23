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

from PyQt5 import QtCore, QtWidgets, uic
import sys

from lib.Speicher import Speicher

class WidgetCodeEntry(QtWidgets.QWidget):
    def __init__(self, mainwindow, newpin = False):
        QtWidgets.QWidget.__init__(self)
        self.mainwindow = mainwindow
        
        self.__mode = 0
        if newpin:
            self.__mode = 1
         
        try:
            self.ui = uic.loadUi('ressource/ui/widget_codeentry.ui', self)
        except:
            print ('Kann UI-Datei nicht laden!')
            sys.exit(1)  
        self.speicher = Speicher()
        self.errorcounter = 0
        self.wakeup_timer = QtCore.QTimer(self)
        self.ui.progress_lock.hide()

        if self.__mode < 2:
            self.ui.button_ok.hide()

        self.ui.label_kopfzeile.setText('Gesperrt: Bitte Code eingeben')
        if self.__mode == 1:
            self.ui.label_kopfzeile.setText(u'Bisheriger Code')

        self.connectSlots()
        

    def update(self):
        self.ui.input_code.clear()
        self.ui.button_ok.hide()
        self.errorcounter = 0
        self.ui.label_kopfzeile.setText('Gesperrt: Bitte Code eingeben')
        if self.__mode == 1:
            self.ui.label_kopfzeile.setText(u'Bisheriger Code')
        if self.__mode == 0:
            self.speicher.lock()


    def check_valid(self, candidate = None):
        if not candidate:
            candidate = str(self.ui.input_code.text())
        if self.__mode == 0:
            if self.speicher.check_password(candidate):
                self.mainwindow.setLocked(False)
                self.ui.input_code.clear()
                return True
        elif self.__mode == 1:
            if self.speicher.check_password(candidate):
                self.currentuser = self.speicher.get_current_user()
                self.ui.label_kopfzeile.setText(u'Neuen Code für %s eingeben' % self.currentuser['name'])
                self.ui.button_ok.show()
                self.__mode = 2
                self.__oldpin = candidate
                self.ui.input_code.clear()
                return True
        return False
                
    def ok(self):
        candidate = str(self.ui.input_code.text())
        if candidate == '':
            # Ignoriere das OK wenn der Code leer ist
            return
        if self.__mode == 2:
            self.ui.label_kopfzeile.setText(u'Neuen Code für %s nochmal eingeben' % self.currentuser['name'])
            self.__mode = 3
            self.__newpin = candidate
            self.ui.input_code.clear()
        elif self.__mode == 3:
            if self.__newpin == candidate:
                self.ui.input_code.clear()
                self.__mode = 1
                self.speicher.set_user_password(self.currentuser['id'], self.currentuser['name'], self.__newpin)
                self.speicher.lock()
                self.mainwindow.reallyLock()

    def numberPressed(self, number):
        def myfunc():
            self.ui.input_code.insert(number)
            if self.__mode < 2:
                self.check_valid()
                
        return myfunc

    def clear(self):
        self.ui.input_code.clear()
        if self.__mode > 1:
            return
        self.errorcounter += 1
        self.ui.progress_lock.show()
        for n in range(10):
            self.ui.__getattribute__('button_%i' % n).setEnabled(False)
        self.ui.button_cancel.setEnabled(False)
        self.ui.label_kopfzeile.setText('Bitte warten...')
        self.wakeup_timer.start(2000 * self.errorcounter)
            
                 
    def awake(self):
        self.wakeup_timer.stop()
        self.ui.input_code.clear()
        for n in range(10):
            self.ui.__getattribute__('button_%i' % n).setEnabled(True)
        self.ui.button_cancel.setEnabled(True)
        self.ui.progress_lock.hide()
        self.ui.label_kopfzeile.setText('Gesperrt: Bitte Code eingeben')
        
      
    def connectSlots(self):
        self.wakeup_timer.timeout.connect(self.awake)

        for n in range(10):
            getattr(self.ui, "button_%i" % n).clicked.connect(self.numberPressed(str(n)))
        self.ui.button_cancel.clicked.connect(self.clear)
        self.ui.button_ok.clicked.connect(self.ok)
    

