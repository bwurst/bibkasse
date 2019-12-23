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
from lib.Kunde import Kunde
from gui.kundenauswahl_listentry import KundenAuswahlWidget
from gui.kundendaten import showKundendatenDialog
from lib.helpers import formatPhoneNumber

class KundenAuswahlDialog(QtWidgets.QDialog):
    keys = {
        '1': ('1', '!'),
        '2': ('2', u'"'),
        '3': ('3', u'§'),
        '4': ('4', u'€'),
        '5': ('5', u'%'),
        '6': ('6', u'&'),
        '7': ('7', '/'),
        '8': ('8', '('),
        '9': ('9', ')'),
        '0': ('0', '='),
        'ss': (u'ß', '?'),
        'accent': (u'\'', u'\''),
        'q': ('Q', 'Q'),
        'w': ('W', 'W'),
        'e': ('E', 'E'),
        'r': ('R', 'R'),
        't': ('T', 'T'),
        'z': ('Z', 'Z'),
        'u': ('U', 'U'),
        'i': ('I', 'I'),
        'o': ('O', 'O'),
        'p': ('P', 'P'),
        'ue': (u'Ü', u'Ü'),
        'a': ('A', 'A'),
        's': ('S', 'S'),
        'd': ('D', 'D'),
        'f': ('F', 'F'),
        'g': ('G', 'G'),
        'h': ('H', 'H'),
        'j': ('J', 'J'),
        'k': ('K', 'K'),
        'l': ('L', 'L'),
        'oe': (u'Ö', u'Ö'),
        'ae': (u'Ä', u'Ä'),
        'y': ('Y', 'Y'),
        'x': ('X', 'X'),
        'c': ('C', 'C'),
        'v': ('V', 'V'),
        'b': ('B', 'B'),
        'n': ('N', 'N'),
        'm': ('M', 'M'),
        'comma': (',', ';'),
        'dot': ('.', ':'),
        'minus': ('-', '_'),
        'space': (' ', ' '),
        }


    def __init__(self, kunde, neu=True, edit=False):
        # Konstruktor der Superklasse aufrufen
        QtWidgets.QDialog.__init__(self, flags=QtCore.Qt.Window | QtCore.Qt.FramelessWindowHint)
        try:
            self.ui = uic.loadUi('ressource/ui/kundenauswahl.ui', self)
        except:
            print ('Kann UI-Datei nicht laden!')
            sys.exit(1)  
            
        self.showFullScreen()
        
        self.speicher = Speicher()
        
        self.kunde = kunde
        if not self.kunde:
            self.kunde = Kunde()
        
        if not neu:
            self.ui.button_neu.setStyleSheet('display:none;')
            self.ui.button_neu.setEnabled(False)
            
        # Soll am Ende immer ein Fenster zum Bearbetien der Kundendaten ausgerufen werden?
        self.edit = edit
        
        self.shift = False
        self.capslock = False
        self.ui.input_text.setText(u'%s' % self.kunde.getErsteTelefon())
        self.ui.input_text.selectAll()
        self.updateVorschlaege()
        self.updateButtonLabels()
        self.connectSlots()

    def clearInput(self):
        self.ui.input_text.clear()
        self.updateVorschlaege()
      
    def getValue(self):
        currentText = str(self.ui.input_text.text())
        return currentText
    
    def updateVorschlaege(self, foo=None):
        self.ui.listWidget_vorschlaege.blockSignals(True)
        self.ui.listWidget_vorschlaege.clear()
        currentText = str(self.ui.input_text.text()).lower()
        if len(currentText) < 3:
            self.ui.listWidget_vorschlaege.blockSignals(False)
            return
        filteredList = self.speicher.sucheKunde(currentText)
        for item in filteredList:
            entry = KundenAuswahlWidget(item)
            item = QtWidgets.QListWidgetItem()
            item.setSizeHint(QtCore.QSize(300, 90))
            self.ui.listWidget_vorschlaege.addItem(item)
            self.ui.listWidget_vorschlaege.setItemWidget(item, entry)    
        self.ui.listWidget_vorschlaege.blockSignals(False)
    
    def keyPressed(self, key):
        return lambda : self.realKeyPressed(key)
    
    def realKeyPressed(self, key):
        index = 0
        if self.shift:
            index = 1
        if key in self.keys.keys():
            self.ui.input_text.insert(self.keys[key][index])
            if self.shift and not self.capslock:
                self.toggleShift()
        elif key == 'backspace':
            self.ui.input_text.backspace()
        self.cursorPositionChanged()
            
    def cursorPositionChanged(self, int1 = 0, int2 = 0):
        # In diesem Dialogfeld brauchen wir keine automatische Umschaltung auf Großbuchstaben
        pass
      
    def capslockClicked(self):
        self.capslock = not self.capslock
        self.shift = self.capslock
        self.ui.button_capslock.setChecked(self.capslock)
        self.updateButtonLabels()
      
    def toggleShift(self):
        self.shift = not self.shift
        self.ui.button_shiftl.setChecked(self.shift)
        self.ui.button_shiftr.setChecked(self.shift)
        if not self.shift:
            self.capslock = False
            self.ui.button_capslock.setChecked(False)
        self.updateButtonLabels()
      
    def updateButtonLabels(self):
        index = 0
        if self.shift:
            index = 1
        for key in self.keys.keys():
            label = self.keys[key][index]
            # Ein & markiert einen Hotkey, das muss verdoppelt werden
            if label == '&':
                label = '&&'
            getattr(self.ui, 'button_%s' % key).setText(label)
        
    def listItemClicked(self, listItem):
        if not listItem:
            return
        widget = self.ui.listWidget_vorschlaege.itemWidget(listItem)
        kunde = widget.kunde
        self.kunde = kunde
        self.ok()
    
    def neu(self):
        currentText = str(self.ui.input_text.text())
        self.kunde = Kunde()
        # Neuen Kunde anlegen
        if currentText.isdigit():
            self.kunde.addKontakt('telefon', currentText)
        else:
            self.kunde.setName(currentText.title())
        self.kunde = showKundendatenDialog(self.kunde)
        if self.kunde:
            self.speicher.speichereKunde(self.kunde)
        self.close()
    
    def ok(self):
        print('ok(edit=%s)' % self.edit)
        if not self.kunde:
            # Wenn nur ein Kunde in der Auswahlliste ist, ist es der
            if self.ui.listWidget_vorschlaege.count() == 1:
                widget = self.ui.listWidget_vorschlaege.itemWidget(self.ui.listWidget_vorschlaege.item(0))
                self.kunde = widget.kunde
            else:
                QtWidgets.QMessageBox.warning(self, u'Fehler', u'Kein Kunde gewählt', buttons=QtWidgets.QMessageBox.Ok, defaultButton=QtWidgets.QMessageBox.Ok)
                return
        if self.edit:
            self.kunde = showKundendatenDialog(self.kunde)
            self.speicher.speichereKunde(self.kunde)
        self.close()
      
    def connectSlots(self):
        for key in self.keys.keys():
            if getattr(self.ui, 'button_%s' % key):
                getattr(self.ui, 'button_%s' % key).clicked.connect(self.keyPressed(key))
            else:
                print ('unknown button: button_%s' % key)
        
        self.ui.button_backspace.clicked.connect(self.keyPressed('backspace'))
        self.ui.button_clear.clicked.connect(self.clearInput)
        self.ui.button_cancel.clicked.connect(self.close)
        self.ui.button_neu.clicked.connect(self.neu)
        self.ui.button_enter.clicked.connect(self.ok)
        self.ui.button_shiftl.clicked.connect(self.toggleShift)
        self.ui.button_shiftr.clicked.connect(self.toggleShift)
        self.ui.button_capslock.clicked.connect(self.capslockClicked)
        #self.ui.listWidget_vorschlaege.currentTextChanged.connect(self.listItemClicked)
        self.ui.input_text.textChanged[str].connect(self.updateVorschlaege)
        self.ui.input_text.cursorPositionChanged[int, int].connect(self.cursorPositionChanged)
        self.ui.input_text.selectionChanged.connect(self.cursorPositionChanged)
        self.ui.listWidget_vorschlaege.itemClicked.connect(self.listItemClicked)
        #self.ui.listWidget_vorschlaege.currentItemChanged.connect(self.listItemClicked)
    
    
    

def showKundenAuswahlDialog(kunde=None, neu=True, edit=False):
    dialog = KundenAuswahlDialog(kunde, neu=neu, edit=edit)
    dialog.show()
    dialog.exec_() # blockiert bis der Dialog geschlossen wird
    return dialog.kunde
    



if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    print ('Mein Text:', showKundenAuswahlDialog())
  

