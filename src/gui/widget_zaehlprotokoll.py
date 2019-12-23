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


from lib.helpers import getMoneyValue
from lib.Speicher import Speicher
from lib.Statistik import tagesstatistik

class WidgetZaehlprotokoll(QtWidgets.QWidget):
    def __init__(self, mainwindow):
        QtWidgets.QWidget.__init__(self)
        self.mainwindow = mainwindow
        
        try:
            self.ui = uic.loadUi('ressource/ui/widget_zaehlprotokoll.ui', self)
        except:
            print ('Kann UI-Datei nicht laden!')
            sys.exit(1)  
        
        self.connectSlots()
        self.__kassenbestand = 0.0
        self.__tageseinnahmen = 0.0

    def isShown(self):
        self.get_tageseinnahmen()
        
        
    def get_tageseinnahmen(self):
        s = Speicher()
        today = datetime.date.today().isoformat()
        journal = s.listZahlungenTagesjournal(today)
        self.__tageseinnahmen = 0.0
        for zahlung in journal:
            self.__tageseinnahmen += zahlung['betrag']
        

    def connectSlots(self):
        self.ui.count_500.valueChanged.connect(self.update)
        self.ui.count_200.valueChanged.connect(self.update)
        self.ui.count_100.valueChanged.connect(self.update)
        self.ui.count_50.valueChanged.connect(self.update)
        self.ui.count_20.valueChanged.connect(self.update)
        self.ui.count_10.valueChanged.connect(self.update)
        self.ui.count_5.valueChanged.connect(self.update)
        self.ui.count_2.valueChanged.connect(self.update)
        self.ui.count_1.valueChanged.connect(self.update)
        self.ui.count_050.valueChanged.connect(self.update)
        self.ui.count_020.valueChanged.connect(self.update)
        self.ui.count_010.valueChanged.connect(self.update)
        self.ui.count_005.valueChanged.connect(self.update)
        self.ui.count_002.valueChanged.connect(self.update)
        self.ui.count_001.valueChanged.connect(self.update)
        self.ui.button_drucken.clicked.connect(self.drucken)
        
    def drucken(self):
        print ('Ich soll drucken')
        
    def update(self, foo=None):
        _summe = 0.0
        _scheine = 0.0
        summe_500 = self.ui.count_500.value() * 500
        self.ui.summe_500.setText(getMoneyValue(summe_500))
        _summe += summe_500
        _scheine += summe_500
        summe_200 = self.ui.count_200.value() * 200
        self.ui.summe_200.setText(getMoneyValue(summe_200))
        _summe += summe_200
        _scheine += summe_200
        summe_100 = self.ui.count_100.value() * 100
        self.ui.summe_100.setText(getMoneyValue(summe_100))
        _summe += summe_100
        _scheine += summe_100
        summe_50 = self.ui.count_50.value() * 50
        self.ui.summe_50.setText(getMoneyValue(summe_50))
        _summe += summe_50
        _scheine += summe_50
        summe_20 = self.ui.count_20.value() * 20
        self.ui.summe_20.setText(getMoneyValue(summe_20))
        _summe += summe_20
        _scheine += summe_20
        summe_10 = self.ui.count_10.value() * 10
        self.ui.summe_10.setText(getMoneyValue(summe_10))
        _summe += summe_10
        _scheine += summe_10
        summe_5 = self.ui.count_5.value() * 5
        self.ui.summe_5.setText(getMoneyValue(summe_5))
        _summe += summe_5
        _scheine += summe_5
        
        self.ui.summe_scheine.setText(getMoneyValue(_scheine))

        _muenzen = 0.0        
        summe_2 = self.ui.count_2.value() * 2
        self.ui.summe_2.setText(getMoneyValue(summe_2))
        _summe += summe_2
        _muenzen += summe_2
        summe_1 = self.ui.count_1.value()
        self.ui.summe_1.setText(getMoneyValue(summe_1))
        _summe += summe_1
        _muenzen += summe_1
        summe_050 = 0.50 * self.ui.count_050.value()
        self.ui.summe_050.setText(getMoneyValue(summe_050))
        _summe += summe_050
        _muenzen += summe_050
        summe_020 = 0.20 * self.ui.count_020.value()
        self.ui.summe_020.setText(getMoneyValue(summe_020))
        _summe += summe_020
        _muenzen += summe_020
        summe_010 = 0.10 * self.ui.count_010.value()
        self.ui.summe_010.setText(getMoneyValue(summe_010))
        _summe += summe_010
        _muenzen += summe_010
        summe_005 = 0.05 * self.ui.count_005.value()
        self.ui.summe_005.setText(getMoneyValue(summe_005))
        _summe += summe_005
        _muenzen += summe_005
        summe_002 = 0.02 * self.ui.count_002.value()
        self.ui.summe_002.setText(getMoneyValue(summe_002))
        _summe += summe_002
        _muenzen += summe_002
        summe_001 = 0.01 * self.ui.count_001.value()
        self.ui.summe_001.setText(getMoneyValue(summe_001))
        _summe += summe_001
        _muenzen += summe_001
        
        self.__kassenbestand = _summe
        
        self.ui.summe_muenzen.setText(getMoneyValue(_muenzen))
        self.ui.summe_alles.setText(getMoneyValue(self.__kassenbestand))
        self.ui.einnahmen.setText(getMoneyValue(self.__tageseinnahmen))
        self.ui.differenz.setText(getMoneyValue(self.__kassenbestand - self.__tageseinnahmen))

