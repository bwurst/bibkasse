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

class TextInputDialog(QtWidgets.QDialog):
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
        'q': ('q', 'Q'),
        'w': ('w', 'W'),
        'e': ('e', 'E'),
        'r': ('r', 'R'),
        't': ('t', 'T'),
        'z': ('z', 'Z'),
        'u': ('u', 'U'),
        'i': ('i', 'I'),
        'o': ('o', 'O'),
        'p': ('p', 'P'),
        'ue': (u'ü', u'Ü'),
        'a': ('a', 'A'),
        's': ('s', 'S'),
        'd': ('d', 'D'),
        'f': ('f', 'F'),
        'g': ('g', 'G'),
        'h': ('h', 'H'),
        'j': ('j', 'J'),
        'k': ('k', 'K'),
        'l': ('l', 'L'),
        'oe': (u'ö', u'Ö'),
        'ae': (u'ä', u'Ä'),
        'y': ('y', 'Y'),
        'x': ('x', 'X'),
        'c': ('c', 'C'),
        'v': ('v', 'V'),
        'b': ('b', 'B'),
        'n': ('n', 'N'),
        'm': ('m', 'M'),
        'comma': (',', ';'),
        'dot': ('.', ':'),
        'minus': ('-', '_'),
        'space': (' ', ' '),
        }


    def __init__(self, kopfzeile, vorschlaege = [], vorgabe = ''):
        # Konstruktor der Superklasse aufrufen
        QtWidgets.QDialog.__init__(self, flags=QtCore.Qt.Window | QtCore.Qt.FramelessWindowHint)
        try:
            self.ui = uic.loadUi('ressource/ui/textinput.ui', self)
        except:
            print ('Kann UI-Datei nicht laden!')
            sys.exit(1)  
            
        self.showFullScreen()
        
        self.vorschlaege = vorschlaege
        self.vorgabe = vorgabe
        self.shift = False
        self.capslock = False
        self.ui.label_kopfzeile.setText(kopfzeile)
        self.ui.input_text.setText(u'%s' % vorgabe)
        self.ui.input_text.selectAll()
        self.updateVorschlaege()
        self.connectSlots()
        self.toggleShift() # Am Anfang groß schreiben
      
    def getValue(self):
        currentText = str(self.ui.input_text.text())
        return currentText
    
    def updateVorschlaege(self, foo=None):
        currentText = str(self.ui.input_text.text()).lower()
        filteredList = []
        for item in self.vorschlaege:
            if item.lower().startswith(currentText):
                filteredList.append(item)
        self.ui.listWidget_vorschlaege.clear()
        for item in filteredList:
            self.ui.listWidget_vorschlaege.addItem(item)
    
    
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
        if len(self.ui.input_text.text()) == 0 or self.ui.input_text.cursorPosition() == 0:
            if not self.shift:
                self.toggleShift()
        else:
            if self.ui.input_text.text()[self.ui.input_text.cursorPosition()-1] in [' ', ',', '-']:
                if not self.shift:
                    self.toggleShift()
            else:
                if self.shift:
                    self.toggleShift()
      
      
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
        if listItem:
            self.ui.input_text.setText(listItem)
            self.ui.input_text.selectAll()
            self.ok()
    
    def ok(self):
        self.close()
      
    def connectSlots(self):
        for key in self.keys.keys():
            getattr(self.ui, 'button_%s' % key).clicked.connect(self.keyPressed(key))
        
        self.ui.button_backspace.clicked.connect(self.keyPressed('backspace'))
        self.ui.button_ok.clicked.connect(self.ok)
        self.ui.button_enter.clicked.connect(self.ok)
        self.ui.button_shiftl.clicked.connect(self.toggleShift)
        self.ui.button_shiftr.clicked.connect(self.toggleShift)
        self.ui.button_capslock.clicked.connect(self.capslockClicked)
        self.ui.listWidget_vorschlaege.currentTextChanged[str].connect(self.listItemClicked)
        self.ui.input_text.textChanged[str].connect(self.updateVorschlaege)
        self.ui.input_text.cursorPositionChanged.connect(self.cursorPositionChanged)
        self.ui.input_text.selectionChanged.connect(self.cursorPositionChanged)
    
    
    

def showTextInputDialog(titel, vorschlaege, vorgabewert):
    dialog = TextInputDialog(titel, vorschlaege, vorgabewert)
    dialog.show()
    dialog.exec_() # blockiert bis der Dialog geschlossen wird
    return dialog.getValue()
    



if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    print ('Mein Text:', showTextInputDialog('Texteingabe', ['a', 'b', 'c'], 'Vorgabe'))
  

