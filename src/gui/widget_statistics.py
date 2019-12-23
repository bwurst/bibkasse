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

from PyQt5 import QtWidgets, QtCore, uic
import sys, datetime
from lib import Statistik
from lib import Speicher

class WidgetStatistics(QtWidgets.QWidget):
    def __init__(self, mainwindow):
        QtWidgets.QWidget.__init__(self)
        self.mainwindow = mainwindow
        
        try:
            self.ui = uic.loadUi('ressource/ui/widget_statistics.ui', self)
        except:
            print ('Kann UI-Datei nicht laden!')
            sys.exit(1)  
        
        self.connectSlots()

    def connectSlots(self):
        self.ui.button_altekunden.clicked.connect(self.erzeugeAlteKunden)
        self.ui.button_rechnungsadressen.clicked.connect(self.erzeugeListeRechnungsadressen)

    def update(self):
        self.year = str(datetime.date.today().year)
        years = sorted(list(Speicher.Speicher().list_years()))

        try:
            self.ui.combo_year.currentIndexChanged.disconnect()
        except TypeError:
            pass
        self.ui.combo_year.clear()
        for y in years:
            self.ui.combo_year.addItem(y)
        self.ui.combo_year.setCurrentIndex(self.ui.combo_year.findText(self.year))
        self.ui.combo_year.currentIndexChanged.connect(self.updateContent)
        self.updateContent()
        
    def updateContent(self):
        self.year = str(self.ui.combo_year.currentText())
        self.ui.textBrowser_jahresstatistik.setHtml( Statistik.html_jahresstatistik(self.year) )
        self.ui.textBrowser_tagesstatistik.setHtml( Statistik.html_tagesstatistik(self.year) )

    def erzeugeAlteKunden(self):
        s = Speicher.Speicher(self.year)
        kunden = s.listeKundennamen()
        s.speichereAlteKunden(kunden)

    def erzeugeListeRechnungsadressen(self):
        s = Speicher.Speicher(self.year)
        kunden = s.listeRechnungsadressen()
        s.speichereAlteRechnungsadressen(kunden)



