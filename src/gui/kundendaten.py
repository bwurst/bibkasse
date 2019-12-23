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

from lib.Kunde import Kunde
from lib.helpers import formatPhoneNumber

from gui.phonenumberinput import showPhoneNumberInputDialog

class KundendatenDialog(QtWidgets.QDialog):
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


    def __init__(self, kunde):
        # Konstruktor der Superklasse aufrufen
        QtWidgets.QDialog.__init__(self, flags=QtCore.Qt.Window | QtCore.Qt.FramelessWindowHint)
        try:
            self.ui = uic.loadUi('ressource/ui/kundendaten.ui', self)
        except:
            print ('Kann UI-Datei nicht laden!')
            sys.exit(1)  
            
        self.showFullScreen()
        
        
        self.kunde = kunde
        if not self.kunde:
            self.kunde = Kunde()

        oeko_kontrollstellen = [
                                u"DE-ÖKO-001 (BCS Öko-Garantie)",
                                u"DE-ÖKO-003 (Lacon)",
                                u"DE-ÖKO-005 (IMO)",
                                u"DE-ÖKO-006 (ABCERT)",
                                u"DE-ÖKO-007 (Prüfverein Ökologische Landbauprodukte)",
                                u"DE-ÖKO-009 (LC Landwirtschafts-Consulting)",
                                u"DE-ÖKO-012 (AGRECO)",
                                u"DE-ÖKO-013 (QC & I)",
                                u"DE-ÖKO-021 (Grünstempel)",
                                u"DE-ÖKO-022 (Kontrollverein ökologischer Landbau)",
                                u"DE-ÖKO-024 (Ecocert)",
                                u"DE-ÖKO-034 (Fachgesellschaft ÖKO-Kontrolle)",
                                u"DE-ÖKO-037 (ÖKOP)",
                                u"DE-ÖKO-039 (GfRS)",
                                u"DE-ÖKO-044 (Ars Probata)",
                                u"DE-ÖKO-060 (QAL)",
                                u"DE-ÖKO-064 (ABC GmbH)",
                                u"DE-ÖKO-070 (Peterson CU)",
                                ]
        for kst in oeko_kontrollstellen:
            self.ui.combo_biokontrollstelle.addItem(kst)
        
        
        self.shift = False
        self.capslock = False
        self.fillTelefon()
        self.fillInputs()
        self.currentInput = self.ui.input_nachname
        self.currentInput.setFocus()
        self.update()
        self.connectSlots()
        self.toggleShift(True) # Am Anfang groß schreiben
      
    def fillInputs(self):
        if self.kunde['firma']:
            self.ui.input_firma.setText(self.kunde['firma'])
        if self.kunde['vorname']:
            self.ui.input_vorname.setText(self.kunde['vorname'])
        if self.kunde['nachname']:
            self.ui.input_nachname.setText(self.kunde['nachname'])
        if self.kunde['strasse']:
            self.ui.input_strasse.setText(self.kunde['strasse'])
        if self.kunde['plz']:
            self.ui.input_plz.setText(self.kunde['plz'])
        if self.kunde['ort']:
            self.ui.input_ort.setText(self.kunde['ort'])
        if self.kunde.isBio():
            self.ui.button_bio.setChecked(True)
            self.ui.combo_biokontrollstelle.setEnabled(True)
            kst = self.kunde.getOekoKontrollstelle()
            idx = self.ui.combo_biokontrollstelle.findText(kst, flags=QtCore.Qt.MatchStartsWith)
            if idx == -1:
                self.ui.combo_biokontrollstelle.setEditText(kst)
            else:
                self.ui.combo_biokontrollstelle.setCurrentIndex(idx)
        else:
            self.ui.button_bio.setChecked(False)
            self.ui.combo_biokontrollstelle.clearEditText()
            self.ui.combo_biokontrollstelle.setEnabled(False)
            
      
    def fillTelefon(self):
        telefon = set()
        for t in self.kunde.listKontakte():
            if t['typ'] in ['mobil', 'telefon']:
                telefon.add(formatPhoneNumber(t['wert']))
        self.ui.input_telefon.setText(' / '.join(telefon))
      
    def keyPressed(self, key):
        return lambda : self.realKeyPressed(key)
    
    def realKeyPressed(self, key):
        index = 0
        if self.shift:
            index = 1
        if key in self.keys.keys():
            self.currentInput.insert(self.keys[key][index])
            if self.shift and not self.capslock:
                self.toggleShift()
        elif key == 'backspace':
            self.currentInput.backspace()
        self.cursorPositionChanged()
            
    def cursorPositionChanged(self, int1 = 0, int2 = 0):
        if self.ui.input_plz == self.currentInput:
            self.toggleShift(False)
            return
        if len(self.currentInput.text()) == 0 or self.currentInput.cursorPosition() == 0:
            self.toggleShift(True)
        else:
            if self.ui.input_strasse == self.currentInput and self.currentInput.text()[self.currentInput.cursorPosition()-1] == ' ':
                # Bei der Straße wird am Anfang groß geschrieben, nicht aber nach einem Leerzeichen
                self.toggleShift(False)
                return
            if self.currentInput.text()[self.currentInput.cursorPosition()-1] in [' ', ',', '-']:
                self.toggleShift(True)
            else:
                self.toggleShift(False)
      
      
    def capslockClicked(self):
        self.capslock = not self.capslock
        self.shift = self.capslock
        self.ui.button_capslock.setChecked(self.capslock)
        self.updateButtonLabels()
      
    def toggleShift(self, state=None):
        if state == False or state == True:
            # None ist beides nicht
            self.shift = bool(state)
        else:
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
        
    def ok(self):
        self.kunde.setName(firma=str(self.ui.input_firma.text()), vorname=str(self.ui.input_vorname.text()), nachname=str(self.ui.input_nachname.text()))
        self.kunde.setAdresse(strasse=str(self.ui.input_strasse.text()), plz=str(self.ui.input_plz.text()), ort=str(self.ui.input_ort.text()))
        kst = str(self.ui.combo_biokontrollstelle.currentText())
        if '(' in kst:
            kst = kst[:kst.find('(')].strip() 
        self.kunde.setOekoKontrollstelle(kst)
        self.close()
      
    def focusChange(self, new):
        if new == self.ui.input_telefon:
            showPhoneNumberInputDialog(self.kunde)
            self.fillTelefon()
        elif type(new) == QtWidgets.QLineEdit:
            self.currentInput = new
            self.cursorPositionChanged()
        elif type(new) == QtWidgets.QComboBox:
            self.currentInput = new.lineEdit()
            self.cursorPositionChanged()
        

    def focusSlot(self, widget):
        def func():
            self.focusChange(widget)
        return func

    def eventFilter(self, qobject, qevent):
        if qevent.type() == QtCore.QEvent.MouseButtonPress:
            qobject.clicked()
        return False
    
      
    def connectSlots(self):
        for key in self.keys.keys():
            getattr(self.ui, 'button_%s' % key).clicked.connect(self.keyPressed(key))
        
        self.ui.button_backspace.clicked.connect(self.keyPressed('backspace'))
        self.ui.button_ok.clicked.connect(self.ok)
        self.ui.button_enter.clicked.connect(self.ok)
        self.ui.button_shiftl.clicked.connect(self.toggleShift)
        self.ui.button_shiftr.clicked.connect(self.toggleShift)
        self.ui.button_capslock.clicked.connect(self.capslockClicked)
        
        self.ui.input_firma.clicked = self.focusSlot(self.ui.input_firma)
        self.ui.input_firma.installEventFilter(self)
        self.ui.input_vorname.clicked = self.focusSlot(self.ui.input_vorname)
        self.ui.input_vorname.installEventFilter(self)
        self.ui.input_nachname.clicked = self.focusSlot(self.ui.input_nachname)
        self.ui.input_nachname.installEventFilter(self)
        self.ui.input_telefon.clicked = self.focusSlot(self.ui.input_telefon)
        self.ui.input_telefon.installEventFilter(self)
        self.ui.input_strasse.clicked = self.focusSlot(self.ui.input_strasse)
        self.ui.input_strasse.installEventFilter(self)
        self.ui.input_plz.clicked = self.focusSlot(self.ui.input_plz)
        self.ui.input_plz.installEventFilter(self)
        self.ui.input_ort.clicked = self.focusSlot(self.ui.input_ort)
        self.ui.input_ort.installEventFilter(self)
        self.ui.combo_biokontrollstelle.clicked = self.focusSlot(self.ui.combo_biokontrollstelle)
        self.ui.combo_biokontrollstelle.installEventFilter(self)
        

def showKundendatenDialog(kunde = None):
    dialog = KundendatenDialog(kunde)
    dialog.show()
    dialog.exec_() # blockiert bis der Dialog geschlossen wird
    return dialog.kunde
    



if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    k = Kunde()
    showKundendatenDialog(k)
    print (k)

