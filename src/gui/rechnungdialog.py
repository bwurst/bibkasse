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
import cups

from gui.textinput import showTextInputDialog 
from gui.kundendaten import showKundendatenDialog

from lib.Speicher import Speicher
from lib.BelegHTML import BelegHTML
from lib.BelegRechnung import BelegRechnung
from lib.BioBeleg import BioBeleg 

PRINTER_OPTIONS = {'media': 'A4',
                   'copies': '1',
                   'sides': 'one-sided',
                   'InputSlot': 'Internal'}

#KONTROLLSTELLEN = ['DE-ÖKO-001 (BCS Öko-Garantie)', 'DE-ÖKO-003 (Lacon)', 'DE-ÖKO-005 (IMO Instit. f. Marktökologie)', 
#                   'DE-ÖKO-006 (ABCERT AG)', 'DE-ÖKO-007 (Prüfverein ökol. Produkte)', 'DE-ÖKO-009 (LC Landwirtschafts-Consulting)',
#                   'DE-ÖKO-012 (AGRECO Göderz GmbH)', 'DE-ÖKO-013 (QC+I)', 'DE-ÖKO-021 (Grünstempel)', 
#                   'DE-ÖKO-022 (Kontrollverein Ökolandbau)', 'DE-ÖKO-024 (Ecocert)', 'DE-ÖKO-034 (Fachverein Öko-Kontrolle)',
#                   'DE-ÖKO-037 (ÖKOP Zertifizierungs GmbH)', 'DE-ÖKO-044 (Ars Probata)', 'DE-ÖKO-064 (ABCG Agrarberatungs GmbH)',
#                   'DE-ÖKO-070 (PCU)',
#                  ]



def showRechnungDialog(invoice, originale = []):
    dlg = RechnungDialog(invoice, originale)
    dlg.show()
    return dlg.exec_()
    
    


class RechnungDialog(QtWidgets.QDialog):
    def __init__(self, invoice, originale = []):
        # Konstruktor der Superklasse aufrufen
        QtWidgets.QDialog.__init__(self, flags=QtCore.Qt.Window | QtCore.Qt.FramelessWindowHint)
        try:
            self.ui = uic.loadUi('ressource/ui/rechnung.ui', self)
        except:
            print ('Kann UI-Datei nicht laden!')
            sys.exit(1)

        self.showFullScreen()
        
        self.beleg = invoice
        if len(originale) < 1:
            originale = [invoice,]
        self.originale = originale
        self.speicher = Speicher()

        self.ui.textEdit_adresse.setText(self.beleg.kunde.getAdresse())
        
        bio_lieferscheine = self.speicher.getBioLieferscheine()
        self.bio_lieferscheine = {}
        
        self.ui.combo_bioanlieferung.clear()
        for l in bio_lieferscheine:
            self.bio_lieferscheine[str(l['id'])] = l
            obstart = ','.join([x.capitalize() for x in l['obstart'] if l['obstart'][x]])
            name = l['adresse'].replace('\n', ',')
            if l['kunde']:
                kunde = self.speicher.ladeKunde(l['kunde'])
                name = kunde.getName()
            
            if l['abholdatum'] == None:
                self.ui.combo_bioanlieferung.addItem("%s: %s, %s %s\n%s - %s" % (l['id'], l['anlieferdatum'], l['menge'], obstart, name, l['kontrollstelle']))
        
        self.ui.combo_bioanlieferung.currentIndexChanged[str].connect(self.bioanlieferungChanged)
        if self.beleg.isBio():
            self.ui.button_bio.setChecked(True)


        
        text = BelegHTML(self.beleg, public=False)
        self.ui.textBrowser.setHtml(text)
        
        self.ui.button_ok.clicked.connect(self.ok)
        self.ui.button_abbrechen.clicked.connect(self.cancel)
        if len(self.originale) > 1:
            self.ui.button_kundendaten.setEnabled(False)
        else:
            self.ui.button_kundendaten.clicked.connect(self.edit_kundendaten)
        self.update()

    def bioanlieferungChanged(self):
        daten = self.ui.combo_bioanlieferung.currentText()
        id = str(daten).split(':')[0]
        adresse = self.bio_lieferscheine[id]['adresse']
        self.ui.textEdit_adresse.setText(adresse)

    def edit_kundendaten(self):
        self.beleg.kunde = showKundendatenDialog(self.beleg.kunde)
        self.speicher.speichereKunde(self.beleg.kunde)
        self.ui.textEdit_adresse.setText(self.beleg.kunde.getAdresse())

    def cancel(self):
        self.reject()
        
    def ok(self):
        print ('ok clicked')
        rechnungsadresse = str(self.ui.textEdit_adresse.toPlainText())
        if self.ui.button_bio.isChecked():
            index = self.ui.combo_bioanlieferung.currentText().split(':')[0]
            l = self.bio_lieferscheine[str(index)]
            lieferant = l['adresse']
            kontrollstelle = l['kontrollstelle']
            if ' ' in kontrollstelle:
                kontrollstelle = kontrollstelle.split(' ')[0]
            if not kontrollstelle:
                QtWidgets.QMessageBox.warning(self, u'Fehler', u'Bio-Kontrollstellen-Code fehlt!', buttons=QtWidgets.QMessageBox.Ok, defaultButton=QtWidgets.QMessageBox.Ok)
                return None
            for beleg in self.originale:
                beleg.setBio(True, kontrollstelle, lieferant)
            self.beleg.setBio(True, kontrollstelle, lieferant)
        if self.beleg.isBio() and not self.beleg.kunde.getAdresse():
            QtWidgets.QMessageBox.warning(self, u'Fehler', u'Bio-Bescheinigung erfordert eine Adresse!', buttons=QtWidgets.QMessageBox.Ok, defaultButton=QtWidgets.QMessageBox.Ok)
            return None

        filename = BelegRechnung(self.beleg, cash=self.ui.button_bar.isChecked(), originale = self.originale, rechnungsadresse = rechnungsadresse)
        c = cups.Connection()
        c.printFile(c.getDefault(), filename, 'Rechnung %s' % self.beleg.getRechnungsnummer(), PRINTER_OPTIONS)
        if self.beleg.isBio():
            # BIO-Beleg
            for beleg in self.originale:
                filename = BioBeleg(beleg, filename='BIO_%s_%02i.pdf' % (beleg.getRechnungsnummer(), self.originale.index(beleg)))
                c = cups.Connection()
                c.printFile(c.getDefault(), filename, 'Bio-Beleg %s' % beleg.getRechnungsnummer(), PRINTER_OPTIONS)
        self.accept()
            
    
    def update(self):
        pass
        
    def eventFilter(self, qobject, qevent):
        if qevent.type() == QtCore.QEvent.MouseButtonPress:
            qobject.clicked()
        return False
