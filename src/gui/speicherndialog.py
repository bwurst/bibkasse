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
import sys, re

from gui.kundenauswahl import showKundenAuswahlDialog
from gui.kundendaten import showKundendatenDialog
from gui.textinput import showTextInputDialog 

from lib.Speicher import Speicher

class SpeichernDialog(QtWidgets.QDialog):
    def __init__(self, invoice):
        # Konstruktor der Superklasse aufrufen
        QtWidgets.QDialog.__init__(self, flags=QtCore.Qt.Window | QtCore.Qt.FramelessWindowHint)
        try:
            self.ui = uic.loadUi('ressource/ui/speicherndialog.ui', self)
        except:
            print ('Kann UI-Datei nicht laden!')
            sys.exit(1)

        self.showFullScreen()
        
        self.kunde_nimmt_mit = False
        self.vorgang = invoice
        if not self.vorgang.ID:
            self.ui.groupBox_ersetzen.setVisible(False)
        if self.vorgang.ID:
            self.ui.button_regalschild_ja.setChecked(False)
            self.ui.button_regalschild_nein.setChecked(True)
        self.ui.widget_regal.setVisible(True)
        self.ui.widget_regaldetails.setVisible(False)
        
        self.ui.widget_bio.setVisible(False)
        self.ui.widget_biodetails.setVisible(False)
        
        self.isBio = False
        if self.vorgang.kunde.isBio():
            self.isBio = True
            self.ui.widget_bio.setVisible(True)
            self.ui.button_bio_ja.setChecked(True)
            self.ui.button_bio_nein.setChecked(False)
            self.ui.widget_biodetails.setVisible(True)
            
            speicher = Speicher()
            bio_lieferscheine = speicher.getBioLieferscheine(kunde=self.vorgang.kunde, fertige=False)
            # Wenn man einen Vorgang bearbeitet, der schon als Bio markiert ist, dann fliegt dieser 
            # Liefeschein aus der Liste heraus weil schon benutzt. Das darf nicht dazu führen, 
            # dass der Vorgang dann also nicht-bio markiert wird
            if self.vorgang.isBio() and self.vorgang.getBioLieferschein():
                l = speicher.ladeBioLieferschein(self.vorgang.getBioLieferschein())
                bio_lieferscheine.insert(0, l)

            self.bio_lieferscheine = {}
            if len(bio_lieferscheine) == 0:
                self.isBio = False
                self.ui.widget_bio.setVisible(False)
                self.ui.widget_biodetails.setVisible(False)
            self.ui.combo_bioanlieferung.clear()
            for l in bio_lieferscheine:
                self.bio_lieferscheine[str(l['id'])] = l
                kunde = l['adresse'].replace('\n', ',') 
                if l['kunde']:
                    kunde = speicher.ladeKunde(l['kunde']).getName()
                    
                if l['abholdatum'] == None:
                    obstart = ','.join([x.capitalize() for x in l['obstart'].keys() if l['obstart'][x]])
                    self.ui.combo_bioanlieferung.addItem("%s: %s, %s %s\n%s - %s" % (l['id'], l['anlieferdatum'], l['menge'], obstart, kunde, l['kontrollstelle']))
            self.bioanlieferungChanged()

        
        self.ui.label_kundenname.clicked = self.kundennameClicked
        self.ui.input_kundenname.clicked = self.kundennameClicked
        self.ui.label_abholung.clicked = self.abholungClicked
        self.ui.input_abholung.clicked = self.abholungClicked
        self.ui.label_kundenname.installEventFilter(self)
        self.ui.input_kundenname.installEventFilter(self)
        self.ui.label_abholung.installEventFilter(self)
        self.ui.input_abholung.installEventFilter(self)

        self.ui.button_kundendaten.clicked.connect(self.editKundendaten)
        
        self.ui.button_1.clicked.connect(self.palettenClicked)
        self.ui.button_2.clicked.connect(self.palettenClicked)
        self.ui.button_3.clicked.connect(self.palettenClicked)
        self.ui.button_4.clicked.connect(self.palettenClicked)
        self.ui.button_5.clicked.connect(self.palettenClicked)
        self.ui.button_6.clicked.connect(self.palettenClicked)

        self.ui.input_abholung.editingFinished.connect(self.abholungEditingFinished)
        self.ui.combo_bioanlieferung.currentIndexChanged[str].connect(self.bioanlieferungChanged)
        
        self.ui.button_mitnehmen.clicked.connect(self.mitnehmen)
        self.ui.button_regal.clicked.connect(self.insRegal)
        
        self.ui.button_bio_ja.clicked.connect(self.bio)
        self.ui.button_bio_nein.clicked.connect(self.keinBio)
        
        self.ui.button_ok.clicked.connect(self.ok)
        self.ui.button_abbrechen1.clicked.connect(self.reject)
        self.ui.button_abbrechen2.clicked.connect(self.reject)
        
        self.update()
        
    def ok(self):
        if self.vorgang.getKundenname() == '':
            QtWidgets.QMessageBox.warning(self, u'Fehler', u'Kein Name eingegeben', buttons=QtWidgets.QMessageBox.Ok, defaultButton=QtWidgets.QMessageBox.Ok)
            return
        else:
            self.accept()
            
    def mitnehmen(self):
        self.kunde_nimmt_mit = True
        self.ui.button_regalschild_nein.setChecked(True)
        self.ok()

    def insRegal(self):
        self.ui.widget_regal.setVisible(False)
        self.ui.widget_regaldetails.setVisible(True)
        self.ui.button_regalschild_ja.setChecked(True)

    def gewaehlterBioLieferschein(self):
        if not self.isBio:
            return None
        daten = self.ui.combo_bioanlieferung.currentText()
        id = str(daten).split(':')[0]
        l = self.bio_lieferscheine[id]
        return l

    def bioanlieferungChanged(self):
        l = self.gewaehlterBioLieferschein()
        self.vorgang.setBio(True, l['kontrollstelle'], l['adresse'], l['id'])

    def bio(self):
        self.isBio = True
        self.ui.widget_biodetails.setVisible(True)
        self.bioanlieferungChanged()
    
    def keinBio(self):
        self.isBio = False
        self.vorgang.setBio(False)
        self.ui.widget_biodetails.setVisible(False)
        
    def palettenClicked(self):
        if self.ui.button_1.isChecked():
            self.vorgang.setPaletten(1)
        elif self.ui.button_2.isChecked():
            self.vorgang.setPaletten(2)
        elif self.ui.button_3.isChecked():
            self.vorgang.setPaletten(3)
        elif self.ui.button_4.isChecked():
            self.vorgang.setPaletten(4)
        elif self.ui.button_5.isChecked():
            self.vorgang.setPaletten(5)
        
        
    def abholungClicked(self):
        import datetime
        zeiten = []
        dt = datetime.datetime.now() + datetime.timedelta(hours=2)
        dt -= datetime.timedelta(minutes = dt.minute)
        while dt.hour < 22:
            zeiten.append( dt.strftime('%H:%M') ) 
            dt += datetime.timedelta(minutes=30)
        zeiten.extend( ['Montag', 'Dienstag', 'Mittwoch', 'Donnerstag', 'Freitag', 'Samstag', 'Sonntag'])
        self.vorgang.setAbholung(showTextInputDialog('Abholung', zeiten, self.vorgang.getAbholung()))  
        self.update()
        
    def kundennameClicked(self):
        self.vorgang.kunde = showKundenAuswahlDialog(self.vorgang.kunde)
        self.update()
    
    def editKundendaten(self):
        self.vorgang.kunde = showKundendatenDialog(self.vorgang.kunde)
        s = Speicher()
        s.speichereKunde(self.vorgang.kunde)
        self.update()
    
    def abholungEditingFinished(self):
        self.vorgang.setAbholung( str(self.ui.input_abholung.text()) )
        self.update()

    def update(self):
        if self.vorgang.getKundenname():
            self.ui.input_kundenname.setText(self.vorgang.getKundenname())
        if self.vorgang.getAbholung():
            self.ui.input_abholung.setText(self.vorgang.getAbholung())
        if self.isBio:
            self.ui.button_bio_ja.setChecked(True)
            self.ui.widget_biodetails.setVisible(True)
        else:
            self.ui.button_bio_nein.setChecked(True)
            self.ui.widget_biodetails.setVisible(False)
        if self.vorgang.getPaletten() == 1:
            self.ui.button_1.setChecked(True)
        elif self.vorgang.getPaletten() == 2:
            self.ui.button_2.setChecked(True)
        elif self.vorgang.getPaletten() == 3:
            self.ui.button_3.setChecked(True)
        elif self.vorgang.getPaletten() == 4:
            self.ui.button_4.setChecked(True)
        elif self.vorgang.getPaletten() == 5:
            self.ui.button_5.setChecked(True)
        elif self.vorgang.getPaletten() == 6:
            self.ui.button_6.setChecked(True)
        if self.vorgang.getKundenname() == '':
            self.ui.input_kundenname.setStyleSheet('border-color: red; background-color: #faa;')
            self.ui.button_ok.setEnabled(False)
            self.ui.button_mitnehmen.setEnabled(False)
        else:
            self.ui.input_kundenname.setStyleSheet('')
            self.ui.button_ok.setEnabled(True)
            self.ui.button_mitnehmen.setEnabled(True)

    def belegDrucken(self):
        return self.ui.button_regalschild_ja.isChecked()
        
    def speicherungErsetzen(self):
        if self.vorgang.ID == None:
            return True
        return self.ui.button_ersetzen.isChecked()
        
    def eventFilter(self, qobject, qevent):
        if qevent.type() == QtCore.QEvent.MouseButtonPress:
            qobject.clicked()
        return False

