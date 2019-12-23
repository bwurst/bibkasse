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

from PyQt5 import QtCore, QtWidgets, QtGui, uic
import sys, time

from lib.Speicher import Speicher
from lib.Beep import error_beep
from gui.kundenauswahl import showKundenAuswahlDialog
from gui.kundendaten import showKundendatenDialog
from gui.bioanlieferung import showBioAnlieferungDialog

class WidgetStartpage(QtWidgets.QWidget):
    def __init__(self, mainwindow):
        QtWidgets.QWidget.__init__(self)
        self.mainwindow = mainwindow
        
        try:
            self.ui = uic.loadUi('ressource/ui/widget_startpage.ui', self)
        except:
            print ('Kann UI-Datei nicht laden!')
            sys.exit(1)  

        self.connectSlots()

        lock_icon = QtGui.QIcon('ressource/icons/lock.png')
        self.ui.button_sperren.setIcon(lock_icon)

        self.__lasterror = None
        self.speicher = Speicher()


    def display_error(self, message):
        self.__lasterror = message
        self.update()

    def update(self):
        if len(self.mainwindow.letzte_belege) == 0:
            self.ui.errordisplay.setText('Lade letzte Belege...')
            invoicelist = self.speicher.listBelegeByDateDesc()
            # Speichere direkt in die Liste, damit wir die Liste nicht umdrehen müssen
            self.mainwindow.letzte_belege = invoicelist[:10]
            self.ui.errordisplay.setText('Lade letzte Belege... fertig!')
        if self.__lasterror:
            self.ui.errordisplay.setText(self.__lasterror)
        else:
            self.ui.errordisplay.clear()
            current_user = self.speicher.get_current_user()
            if current_user:
                self.ui.errordisplay.setText('Angemeldet als %s' % current_user['name'])

        
    def action(self, action):
        self.__lasterror = None
        action()

    def action_wrapper(self, target):
        def action():
            self.action(target)
            
        return action
    
    def connectSlots(self):
        self.ui.button_sperren.clicked.connect(self.action_wrapper(self.mainwindow.reallyLock))
       
        self.ui.button_abfuellung.clicked.connect(self.action_wrapper(self.mainwindow.showAbfuellungenWidget))
        self.ui.button_abholung.clicked.connect(self.action_wrapper(self.mainwindow.showHistoryWidget))
        self.ui.button_onlineauftraege.clicked.connect(self.action_wrapper(self.mainwindow.showAuftraegeWidget))
        self.ui.button_kundendaten.clicked.connect(self.kundendaten)
        self.ui.button_verkauf.clicked.connect(self.action_wrapper(self.mainwindow.showVerkaufWidget))
        self.ui.button_etiketten.clicked.connect(self.action_wrapper(self.mainwindow.showLabelsWidget))
        self.ui.button_bioanlieferung.clicked.connect(self.bioAnlieferung)

        self.ui.button_kasse_oeffnen.clicked.connect(self.mainwindow.oeffneKasse)
        self.ui.button_letzte_belege.clicked.connect(self.action_wrapper(self.mainwindow.showLast10Widget))

    
    def kundendaten(self):
        showKundenAuswahlDialog(edit=True)
    
    def bioAnlieferung(self):
        kunde = showKundenAuswahlDialog()
        if not kunde:
            return
        if not kunde.isBio():
            kunde = showKundendatenDialog(kunde)
            self.speicher.speichereKunde(kunde)
        if not kunde.isBio():
            QtWidgets.QMessageBox.warning(self, u'Fehler', u'Der gewählte Kunde ist nicht als Bio-Lieferant eingerichtet!', buttons=QtWidgets.QMessageBox.Ok, defaultButton=QtWidgets.QMessageBox.Ok)
            return
        showBioAnlieferungDialog(kunde)
    

