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



def showRechnungDialog(invoice):
    dlg = RechnungDialog(invoice)
    dlg.show()
    return dlg.exec_()
    
    


class RechnungDialog(QtWidgets.QDialog):
    def __init__(self, invoice):
        # Konstruktor der Superklasse aufrufen
        QtWidgets.QDialog.__init__(self, flags=QtCore.Qt.Window | QtCore.Qt.FramelessWindowHint)
        try:
            self.ui = uic.loadUi('ressource/ui/rechnung.ui', self)
        except:
            print ('Kann UI-Datei nicht laden!')
            sys.exit(1)

        self.showFullScreen()
        
        self.vorgang = invoice
        self.speicher = Speicher()

        self.ui.textEdit_adresse.setText(self.vorgang.kunde.getAdresse())
        
        self.ui.button_ok.clicked.connect(self.ok)
        self.ui.button_abbrechen.clicked.connect(self.cancel)
        self.ui.button_kundendaten.clicked.connect(self.edit_kundendaten)
        self.update()

    def edit_kundendaten(self):
        self.vorgang.kunde = showKundendatenDialog(self.vorgang.kunde)
        self.speicher.speichereKunde(self.vorgang.kunde)
        self.ui.textEdit_adresse.setText(self.vorgang.kunde.getAdresse())

    def cancel(self):
        self.reject()
        
    def ok(self):
        self.vorgang.setRechnungsadresse(str(self.ui.textEdit_adresse.toPlainText()))
        self.accept()

    
    def update(self):
        pass
        
    def eventFilter(self, qobject, qevent):
        if qevent.type() == QtCore.QEvent.MouseButtonPress:
            qobject.clicked()
        return False
