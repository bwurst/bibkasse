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

from lib.helpers import formatPhoneNumber

try:
    (ui_class, ui_base) = uic.loadUiType('ressource/ui/phonenumber_listentry.ui')
except:
    print ('Kann UI-Datei nicht laden!')
    sys.exit(1)


class TelefonnummerWidget(QtWidgets.QFrame):
    def __init__(self, parent, id, number):
        self.parent = parent
        self._id = id
        self.number = number
        self.typ = 'telefon'
        if self.number.startswith('01'):
            self.typ='mobil'
        # Konstruktor der Superklasse aufrufen
        QtWidgets.QFrame.__init__(self)
        
        self.ui = ui_class()
        self.ui.setupUi(self)

        self.ui.lineEdit.setEnabled(False)
        self.ui.lineEdit.setText(formatPhoneNumber(number))
        self.ui.pushButton.clicked.connect(self.delete)

    def backspace(self):
        if len(self.number) > 0:
            self.number = self.number[:-1]
        else:
            self.number = ''
        self.updateNumber()
    
    def numberPressed(self, digit):
        self.number += digit
        self.updateNumber()

    def clear(self):
        self.number = ''
        self.updateNumber()

    def getValue(self):
        return self.number
    
    def getFocus(self):
        self.ui.lineEdit.setEnabled(True)
        self.ui.lineEdit.setStyleSheet('color: #000; background-color: #fff;')
    
    def loseFocus(self):
        self.ui.lineEdit.setEnabled(False)
        self.ui.lineEdit.setStyleSheet('color: #333; background-color: #ddd;')

    def updateNumber(self):
        if self.number == '01':
            self.typ='mobil'
        self.ui.lineEdit.setText(formatPhoneNumber(self.number))
        self.parent.kunde.editKontakt(self._id, self.typ, self.number)
        
    def delete(self):
        self.parent.deleteNumber(self._id)

