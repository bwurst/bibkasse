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

from gui.textinput import showTextInputDialog 
from gui.phonenumberinput import showPhoneNumberInputDialog 

from lib.helpers import formatPhoneNumber

from lib.BelegHTML import BelegHTML
from lib.Speicher import Speicher

Wochentage = ['Montag', 'Dienstag', 'Mittwoch', 'Donnerstag', 'Freitag', 'Samstag', 'Sonntag']


class DialogAnrufen(QtWidgets.QDialog):
    def __init__(self, vorgang):
        # Konstruktor der Superklasse aufrufen
        QtWidgets.QDialog.__init__(self, flags=QtCore.Qt.Window | QtCore.Qt.FramelessWindowHint)
        try:
            self.ui = uic.loadUi('ressource/ui/dialog_anrufen.ui', self)
        except:
            print ('Kann UI-Datei nicht laden!')
            sys.exit(1)

        self.showFullScreen()
        
        self.speicher = Speicher()
        self.vorgang = vorgang
            
        self.ui.button_edit.clicked.connect(self.edit)
        self.ui.button_erreicht.clicked.connect(self.erreicht)
        self.ui.button_ab.clicked.connect(self.ab)
        self.ui.button_nichterreicht.clicked.connect(self.nichterreicht)
        self.ui.button_abbrechen.clicked.connect(self.reject)
        self.update()
        
    def erreicht(self):
        zeiten = ['Sofort', 'Heute Nachmittag', 'Heute Abend', u'Morgen früh', 'Morgen Nachmittag', 'Morgen Abend', '13:00', '18:00', '20:00', '8:00']
        self.vorgang.setAbholung(showTextInputDialog('Abholung', zeiten, ''))  
        self.speicher.speichereVorgang(self.vorgang)
        self.speicher.speichereAnruf(self.vorgang, 'erreicht', 'Abholung: %s' % self.vorgang.getAbholung())
        self.accept()

    def ab(self):
        self.speicher.speichereAnruf(self.vorgang, 'ab', '')
        self.accept()
    
    def nichterreicht(self):
        self.speicher.speichereAnruf(self.vorgang, 'nichterreicht', '')
        self.accept()
    
    def edit(self):
        invoice = self.vorgang
        kunde = invoice.getKunde()
        showPhoneNumberInputDialog(kunde)
        self.speicher.speichereKunde(kunde)
        telefonnummern = ' / '.join([formatPhoneNumber(e['wert']) for e in kunde.listKontakteTelefon()])
        self.ui.label_telefon.setText(telefonnummern)
        
    def update(self):
        invoice = self.vorgang
        kunde = invoice.getKunde()
        if kunde.getName():
            self.ui.label_kundenname.setText(kunde.getName())
        else:
            self.ui.label_kundenname.setText(u'<i>Barverkauf</i>')
        
        zeitpunkt = invoice.getZeitpunkt()
        if zeitpunkt:
            self.ui.label_zeitpunkt.setText('%s, %s Uhr' % (Wochentage[zeitpunkt.weekday()], zeitpunkt.strftime('%d.%m.%Y / %H:%M') ))
        else:
            self.ui.label_zeitpunkt.setText('unbekannt')
        kontakte = kunde.listKontakteTelefon()
        if len(kontakte) == 0:
            showPhoneNumberInputDialog(kunde)
            if len(kunde.listKontakteTelefon()) > 0:
                self.speicher.speichereKunde(kunde)
        telefonnummern = ' / '.join([formatPhoneNumber(e['wert']) for e in kunde.listKontakteTelefon()])
        self.ui.label_telefon.setText(telefonnummern)
        anrufe = self.speicher.getAnrufe(self.vorgang)
        text = u''
        for anruf in anrufe:
            if anruf['ergebnis'] == 'erreicht':
                text += u'%s - Erreicht - %s' % (anruf['timestamp'],anruf['bemerkung'])
            elif anruf['ergebnis'] == 'ab':
                text += u'%s - AB' % (anruf['timestamp'],)
            elif anruf['ergebnis'] == 'nichterreicht':
                text += u'%s - NICHT erreicht' % (anruf['timestamp'],)
            else:
                text += u'%s - %s' % (anruf['ergebnis'], anruf['timestamp'])
            text += '\n'
        self.ui.textBrowser_ergebnisse.setText(text)
        
        html = BelegHTML(self.vorgang)
        self.ui.textBrowser_beleg.setText(html)

    
     