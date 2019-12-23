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
import cups
from gui.kundenauswahl_listentry import KundenAuswahlWidget
import datetime

PRINTER_OPTIONS = {'media': 'A4',
                   'copies': '1',
                   'sides': 'one-sided',
                   'InputSlot': 'Internal'}


from lib.Kunde import Kunde
from lib.Speicher import Speicher
from lib.BioLieferschein import BioLieferschein

class BioAnlieferungDialog(QtWidgets.QDialog):
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
            self.ui = uic.loadUi('ressource/ui/bioanlieferung.ui', self)
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
        self.fillInputs()
        self.currentInput = self.ui.input_menge
        self.currentInput.setFocus()
        kundenwidget = KundenAuswahlWidget(self.kunde)
        kundenwidget.setParent(self.ui.widget_kundendaten)
        kundenwidget.show()
        self.connectSlots()
        self.toggleShift(False) # Klein damit Zahlen sichtbar sind.
      
    def fillInputs(self):
        kst = self.kunde.getOekoKontrollstelle()
        idx = self.ui.combo_biokontrollstelle.findText(kst, flags=QtCore.Qt.MatchStartsWith)
        if idx == -1:
            self.ui.combo_biokontrollstelle.setEditText(kst)
        else:
            self.ui.combo_biokontrollstelle.setCurrentIndex(idx)
        self.ui.dateEdit.setDate(datetime.date.today())
            
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
        # In diesem Dialogfeld brauchen wir keine automatische Umschaltung auf Großbuchstaben
        pass
      
      
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
        
    def cancel(self):
        self.close()
        
    def ok(self):
        kst = str(self.ui.combo_biokontrollstelle.currentText())
        if '(' in kst:
            kst = kst[:kst.find('(')].strip() 
        self.kunde.setOekoKontrollstelle(kst)
        
        anlieferdatum = self.ui.dateEdit.date().toPyDate()
        
        data = {
            'kunde': self.kunde.ID(),
            'adresse': self.kunde.getAdresse(),
            'menge': str(self.ui.input_menge.text()),
            'kontrollstelle': kst,
            'obstart': {},
            'anlieferdatum': anlieferdatum.isoformat(),
            }
        if not data['menge']:
            QtWidgets.QMessageBox.warning(self, u'Fehler', u'Obst-Menge fehlt!', buttons=QtWidgets.QMessageBox.Ok, defaultButton=QtWidgets.QMessageBox.Ok)
            return
        for key in ['apfel', 'birne', 'quitte']:
            if getattr(self.ui, 'button_%s' % key).isChecked():
                data['obstart'][key] = True
        s = Speicher()
        s.speichereBioLieferschein(data)
        pdffile = BioLieferschein(data)
        
        c = cups.Connection()
        c.printFile(c.getDefault(), pdffile, 'Bio-Lieferschein %s' % pdffile, PRINTER_OPTIONS)
        self.close()
      
    def focusChange(self, new):
        self.currentInput = new
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
        self.ui.button_cancel.clicked.connect(self.cancel)
        self.ui.button_enter.clicked.connect(self.ok)
        self.ui.button_shiftl.clicked.connect(self.toggleShift)
        self.ui.button_shiftr.clicked.connect(self.toggleShift)
        self.ui.button_capslock.clicked.connect(self.capslockClicked)
        
        self.ui.input_menge.clicked = self.focusSlot(self.ui.input_menge)
        self.ui.input_menge.installEventFilter(self)
    

def showBioAnlieferungDialog(kunde = None):
    dialog = BioAnlieferungDialog(kunde)
    dialog.show()
    dialog.exec_() # blockiert bis der Dialog geschlossen wird
    return dialog.kunde
    



if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    k = Kunde()
    showBioAnlieferungDialog(k)
    print (k)

